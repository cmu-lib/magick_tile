"""
This takes inspiration heavily from https://github.com/zimeon/iiif/blob/master/iiif_static.py
"""

import os
import re
import sys
import json
import optparse
import subprocess

from tqdm import tqdm
from glob import glob
from math import floor, ceil
from tempfile import TemporaryDirectory

class Tiler:
    # TODO replace this with a much smarter system for iterating potential scaling and reduction sizes
    BASE_SCALING_FACTORS = (1, 2, 4, 8, 16, 32, 64, 128, 256)
    BASE_SMALLER_SIZES = (16, 32, 64, 128, 256, 512, 1024, 2048, 4096)

    def __init__(self, sourcepath, id, tile_size=256):
        if not self.is_magick_installed():
            raise Exception(
                "ImageMagick does not appear to be installed or available on your $PATH"
            )

        self.sourcepath = sourcepath
        self.id = id
        self.tile_size = tile_size

        # Measure the original dimensions of the image, and find the smaller of the two
        self.orig_dims = self.get_dimensions()
        if self.orig_dims[0] > self.orig_dims[1]:
            self.min_dim = self.orig_dims[1]
        else:
            self.min_dim = self.orig_dims[0]

    @staticmethod
    def is_magick_installed():
        """
        Confirm that Imagemagick is installed and on $PATH
        """
        try:
            res = subprocess.run(["convert", "--version"], stdout=subprocess.PIPE)
            return True
        except:
            return False

    def get_scaling_factors(self):
        """
        Compute scaling factors such that the largest tile made is smaller than the shorter dimension of the input image
        """
        return [
            sf
            for sf in self.BASE_SCALING_FACTORS
            if sf < ceil(self.min_dim / self.tile_size)
        ]

    def get_downsizing_levels(self):
        """
        Compute downsizing levels such that the width of the largest reduced image is smaller than the width of the original image
        """
        return [s for s in self.BASE_SMALLER_SIZES if s < self.orig_dims[0]]

    def generate_cropped_tiles(self, output_dir):
        """
        Two-stage generation:

        1. Use convert's -crop function to write tilesets at each of the scaling factors appropriate for the image (e.g. tiles at 256, 512, 1024 px on a side, etc.) Stores intermediate files to a temporary directory
        """
        temp_croppath = TemporaryDirectory()
        for sf in tqdm(self.get_scaling_factors(), desc="Creating scaling levels"):
            cropsize = self.tile_size * sf
            call = [
                "convert",
                self.sourcepath,
                "-monitor",
                "-crop",
                f"{cropsize}x{cropsize}",
                "-set",
                "filename:tile",
                "%[fx:page.x],%[fx:page.y],%[fx:w],%[fx:h]",  # rely on Imagemagick to tell us the resulting dimensions for the tiles it makes, which is especially useful on the non-square tiles from the right and bottom edges of images
                "+repage",
                "+adjoin",
                f"{temp_croppath.name}/{cropsize},{sf},%[filename:tile].jpg",
            ]
            crop_res = subprocess.call(call, stdout=subprocess.PIPE)

        """
        2. Use convert's -resize function to reduce the cropped tiles to the specified tile size. These resized tiles are saved to the specified output directory with the right nested directory structure expected of IIIF tiles.
        """
        for f in tqdm(glob(temp_croppath.name + "/*"), desc="Regularizing all tiles"):
            attrs = [int(i) for i in os.path.basename(f).split(".")[0].split(",")]

            base = attrs[0]
            sf = attrs[1]
            x = attrs[2]
            y = attrs[3]
            w = attrs[4]
            h = attrs[5]

            file_w = ceil(w / sf) if w < self.tile_size * sf else self.tile_size
            file_h = floor(h / sf) if h < self.tile_size * sf else self.tile_size
            target_dir = f"{output_dir}/{x},{y},{w},{h}/{file_w},/0"
            os.makedirs(target_dir)
            res = subprocess.call(
                [
                    "convert",
                    f,
                    "-resize",
                    f"{file_w}x{file_h}",
                    f"{target_dir}/default.jpg",
                ],
                stdout=subprocess.PIPE,
            )
        temp_croppath.cleanup()

    def generate_reduced_versions(self, output_dir):
        """
        Create smaller derivatives of the full image.
        """
        for ds in tqdm(self.get_downsizing_levels(), desc="Reduced versions"):
            target_directory = f"{output_dir}/full/{ds},/0"
            os.makedirs(target_directory)
            res = subprocess.call(
                [
                    "convert",
                    self.sourcepath,
                    "-geometry",
                    f"{ds}x",
                    f"{target_directory}/default.jpg",
                ],
                stdout=subprocess.PIPE,
            )

    def generate_info(self):
        """
        Generate the info.json for this image

        TODO: add ability to list arbitrary endpoint features re https://iiif.io/api/image/2.1/#profile-description
        """
        return {
            "@context": "http://iiif.io/api/image/2/context.json",
            "@id": self.id,
            "profile": [
                "http://iiif.io/api/image/2/level0.json",
                {"formats": ["jpg"], "qualities": ["default"]},
            ],
            "protocol": "http://iiif.io/api/image",
            "sizes": [
                {"width": ds, "height": "full"} for ds in self.get_downsizing_levels()
            ],
            "tiles": [
                {"scaleFactors": self.get_scaling_factors(), "width": self.tile_size}
            ],
            "width": self.orig_dims[0],
            "height": self.orig_dims[1],
        }

    def write_info(self, output_dir):
        json.dump(self.generate_info(), open(f"{output_dir}/info.json", "w"), indent=2)

    def create_iiif_0(self, output_dir):
        """
        Run the tiling, resizes, and info.json generation all together
        """
        os.makedirs(output_dir)
        self.generate_cropped_tiles(output_dir)
        self.generate_reduced_versions(output_dir)
        self.write_info(output_dir)

    def get_dimensions(self):
        """
        Get the dimensions of the sourcepath as [x, y]
        """
        r = subprocess.run(['identify', '-ping', self.sourcepath], capture_output=True)
        s = r.stdout.decode('utf-8')
        dims = re.search('(\d+)x(\d+)', s).groups()
        return [int(d) for d in dims]


def main():
    if sys.version_info < (3, 7):
        sys.exit("This program requires python version 3.7 or later")

    # Options and arguments
    p = optparse.OptionParser(
        description="IIIF Image API Level-0 static file generator",
        usage="usage: %prog [options] file (-h for help)",
    )

    p.add_option(
        "--output",
        "-o",
        default=None,
        action="store",
        help="Destination directory for tiles",
    )

    p.add_option(
        "--identifier",
        "-i",
        default=None,
        action="store",
        help="Image identifier to be written to final info.json (e.g. https://example.com/iiif/my_image)",
    )

    p.add_option(
        "--tilesize",
        "-t",
        default=256,
        action="store",
        type="int",
        help="Tile size to produce [default %default]",
    )

    (opt, sources) = p.parse_args()

    til = Tiler(sourcepath=sources[0], id=opt.identifier, tile_size=opt.tilesize)
    til.create_iiif_0(output_dir=opt.output)


if __name__ == "__main__":
    main()

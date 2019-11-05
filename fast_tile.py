from glob import glob
from tempfile import TemporaryDirectory
import os
import subprocess
from math import floor, ceil
import json
from tqdm import tqdm


class Tiler:
    BASE_SCALING_FACTORS = (1, 2, 4, 8, 16, 32, 64, 128, 256)
    BASE_SMALLER_SIZES = (16, 32, 64, 128, 256, 512, 800, 1024, 2048)

    def __init__(self, sourcepath, output, tile_size=256):
        if not self.is_magick_installed():
            raise EnvironmentError

        self.sourcepath = sourcepath
        self.output = output
        self.tile_size = tile_size
        self.temp_croppath = TemporaryDirectory()
        self.temp_resizepath = TemporaryDirectory()

        self.orig_dims = [
            int(d)
            for d in subprocess.run(
                ["identify", "-ping", f"{self.sourcepath}"], stdout=subprocess.PIPE
            )
            .stdout.decode("utf-8")
            .split(" ")[2]
            .split("x")
        ]

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
            subprocess.run(["convert", "--version"])
            return true
        except:
            return false

    def get_scaling_factors(self):
        return [
            sf
            for sf in self.BASE_SCALING_FACTORS
            if sf < ceil(self.min_dim / self.tile_size)
        ]

    def get_downsizing_levels(self):
        return [s for s in self.BASE_SMALLER_SIZES if s < self.orig_dims[0]]

    def crop_contents(self):
        return glob(self.temp_croppath.name + "/*")

    def generate_cropped_tiles(self):
        for sf in self.get_scaling_factors():
            cropsize = self.tile_size * sf
            call = [
                "convert",
                self.sourcepath,
                "-monitor",
                "-crop",
                f"{cropsize}x{cropsize}",
                "-set",
                "filename:tile",
                "%[fx:page.x],%[fx:page.y],%[fx:w],%[fx:h]",
                "+repage",
                "+adjoin",
                f"{self.temp_croppath.name}/{cropsize},{sf},%[filename:tile].jpg",
            ]
            crop_res = subprocess.run(call, stdout=subprocess.PIPE)

        for f in tqdm(
            glob(self.temp_croppath.name + "*.jpg"), desc="Regularize cropped tiles"
        ):
            attrs = [int(i) for i in os.path.basename(f).split(".")[0].split(",")]

            base = attrs[0]
            sf = attrs[1]
            x = attrs[2]
            y = attrs[3]
            w = attrs[4]
            h = attrs[5]

            file_w = ceil(w / sf) if w < self.tile_size * sf else self.tile_size
            file_h = floor(h / sf) if h < self.tile_size * sf else self.tile_size
            target_dir = f"{self.output}/{x},{y},{w},{h}/{w},/0"
            os.makedirs(target_dir)
            res = subprocess.call(
                [
                    "convert",
                    f,
                    "-resize" f"{file_w}x{file_h}",
                    f"{target_dir}/default.jpg",
                ]
            )

    def generate_reduced_versions(self):
        for ds in self.get_downsizing_levels():
            pass

    def generate_info(self):
        return {
            "@context": "http://iiif.io/api/image/2/context.json",
            "@id": os.path.basename(SOURCE_IMAGE).split(".")[0],
            "profile": [
                "http://iiif.io/api/image/2/level0.json",
                {"formats": ["jpg"], "qualities": ["default"]},
            ],
            "protocol": "http://iiif.io/api/image",
            "sizes": full_dims,
            "tiles": [{"scaleFactors": SCALING_FACTORS, "width": self.tile_size}],
            "width": orig_dims[0],
            "height": orig_dims[1],
        }

    def write_info(self):
        json.dump(self.generate_info(), open(f"{self.output}/info.json", "w"), indent=2)

    def cleanup(self):
        """
        Cleanup the
        """
        self.temp_croppath.cleanup()
        self.temp_resizepath.cleanup()


til = Tiler("ap.png", "output")
til.generate_cropped_tiles()


# self.tile_size = 256
# SOURCE_IMAGE = "prints_drawings.png"
# OUTPUT_DIR = "out/prints_drawings"

# os.makedirs(OUTPUT_DIR)
# os.makedirs(OUTPUT_DIR + "/temp_crops")
# os.makedirs(OUTPUT_DIR + "/temp_resizes")

# orig_dims = [
#     int(d)
#     for d in subprocess.run(
#         ["identify", "-ping", f"{SOURCE_IMAGE}"], stdout=subprocess.PIPE
#     )
#     .stdout.decode("utf-8")
#     .split(" ")[2]
#     .split("x")
# ]

# if orig_dims[0] > orig_dims[1]:
#     min_dim = orig_dims[1]
# else:
#     min_dim = orig_dims[0]


# DOWNSIZING_FACTORS = []
# p = 2
# cont = True
# while cont:
#     DOWNSIZING_FACTORS.append(p)
#     cont = (floor(min_dim / pow(2, p))) > self.tile_size
#     p = p + 1


# im_calls = []
# for sf in SCALING_FACTORS:
#     cropsize = self.tile_size * sf
#     im_calls.append(
#         f'convert {SOURCE_IMAGE} -monitor -crop {cropsize}x{cropsize} -set filename:tile "%[fx:page.x],%[fx:page.y],%[fx:w],%[fx:h]" +repage +adjoin "{OUTPUT_DIR}/temp_crops/{cropsize},{sf},%[filename:tile].jpg"'
#     )

# for call in tqdm(im_calls, desc="Creating tiles"):
#     code = os.system(call)

# image_results = []

# for f in glob(OUTPUT_DIR + "/temp_crops/*.jpg"):
#     attrs = [int(i) for i in os.path.basename(f).split(".")[0].split(",")]
#     image_results.append(
#         {
#             "filename": f,
#             "attributes": {
#                 "base": attrs[0],
#                 "scaling_factor": attrs[1],
#                 "x": attrs[2],
#                 "y": attrs[3],
#                 "w": attrs[4],
#                 "h": attrs[5],
#             },
#         }
#     )

# for i in tqdm(image_results, desc="Regularize cropped tiles"):
#     attrs = i["attributes"]
#     sf = attrs["scaling_factor"]
#     real_x = attrs["x"]
#     real_y = attrs["y"]
#     real_w = attrs["w"]
#     real_h = attrs["h"]
#     file_w = ceil(attrs["w"] / sf) if attrs["w"] < self.tile_size * sf else self.tile_size
#     file_h = floor(attrs["h"] / sf) if attrs["h"] < self.tile_size * sf else self.tile_size
#     target_dir = f"{OUTPUT_DIR}/{real_x},{real_y},{real_w},{real_h}/{file_w},/0"
#     os.makedirs(target_dir)
#     res = os.system(
#         f"convert {i['filename']} -resize {file_w}x{file_h} {target_dir}/default.jpg"
#     )

# downsize_calls = []
# for df in DOWNSIZING_FACTORS:
#     new_w = ceil(orig_dims[0] * 1 / pow(2, df))
#     new_h = ceil(orig_dims[1] * 1 / pow(2, df))
#     downsize_calls.append(
#         f"convert {SOURCE_IMAGE} -resize {new_w}x{new_h} {OUTPUT_DIR}/temp_resizes/{new_w},{new_h}.jpg"
#     )

# for call in tqdm(downsize_calls, desc="Downsizing"):
#     code = os.system(call)

# full_results = glob(OUTPUT_DIR + "/temp_resizes/*.jpg")

# full_dims = []

# for i in full_results:
#     components = os.path.basename(i).split(".")[0].split(",")
#     target_dir = f"{OUTPUT_DIR}/full/{components[0]},/0"
#     os.makedirs(target_dir)
#     os.rename(i, target_dir + "/default.jpg")
#     full_dims.append({"width": int(components[0]), "height": "full"})


# manifest = {
#     "@context": "http://iiif.io/api/image/2/context.json",
#     "@id": os.path.basename(SOURCE_IMAGE).split(".")[0],
#     "profile": [
#         "http://iiif.io/api/image/2/level0.json",
#         {"formats": ["jpg"], "qualities": ["default"]},
#     ],
#     "protocol": "http://iiif.io/api/image",
#     "sizes": full_dims,
#     "tiles": [{"scaleFactors": SCALING_FACTORS, "width": self.tile_size}],
#     "width": orig_dims[0],
#     "height": orig_dims[1],
# }

# json.dump(manifest, open(f"{OUTPUT_DIR}/info.json", "w"), indent=2)

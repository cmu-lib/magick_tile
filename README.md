# magick_tile

[![PyPi version](https://img.shields.io/pypi/v/magick-tile.svg)](https://pypi.org/project/magick-tile/)

This python script relies on Imagemagick to efficiently create derivative tiles of a very large image, and structure them into directories compliant with [IIIF Level 0](https://iiif.io/api/image/2.1/compliance/#level-0-compliance) specification for static sites.

This takes inspiration heavily from https://github.com/zimeon/iiif/blob/master/iiif_static.py, but uses ImageMagick rather than Pillow in order to speed up generation at the expense of a less flexible treatment of images.

## Prerequisites

- Python 3
- [Imagemagick](https://imagemagick.org/index.php) must be available on your path

## Run

```
python3 magick_tile.py --help

> Usage: magick_tile.py [options] file (-h for help)
>
> IIIF Image API Level-0 static file generator
>
> Options:
>   -h, --help            show this help message and exit
>   -o OUTPUT, --output=OUTPUT
>                         Destination directory for tiles
>   -i IDENTIFIER, --identifier=IDENTIFIER
>                         Image identifier to be written to final info.json
>                         (e.g. https://example.com/iiif/my_image)
>   -t TILESIZE, --tilesize=TILESIZE
>                         Tile size to produce [default 256]

python3 magick_tile.py -o apple/ -i "https://example.com/iiif/apple" apple.jpg
```

This will create and populate the specified output directory with tiles from a given image.

N.b. because several of the Imagemagick utilities called here already utilize multiple cores, returns for running this script in parallel diminish rapidly.

---
[Matthew Lincoln](https://matthewlincoln.net)

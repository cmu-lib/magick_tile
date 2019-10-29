# magick_tile

This python script relies on Imagemagick to efficiently create derivative tiles of a very large image, and structure them into directories compliant with [IIIF Level 0](https://iiif.io/api/image/2.1/compliance/#level-0-compliance) specification for static sites.

## Prerequisites

- Python 3
- Imagemagick must be available on your path

## Run

```
python3 fast_tile.py
```

This will create and populate an `out/` directory.

N.b. because several of the Imagemagick utilities called here already utilize multiple cores, returns for running this script in parallel diminish rapidly.

---
[Matthew Lincoln](https://matthewlincoln.net)

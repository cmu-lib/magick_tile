from glob import glob
import os
import subprocess
from math import floor, ceil
import json
from tqdm import tqdm
import asyncio

BASE_TILE = 256
SOURCE_IMAGE = "prints_drawings.png"
OUTPUT_DIR = "out/prints_drawings"

os.makedirs(OUTPUT_DIR)

orig_dims = [
    int(d)
    for d in subprocess.run(
        ["identify", "-ping", f"{SOURCE_IMAGE}"], stdout=subprocess.PIPE
    )
    .stdout.decode("utf-8")
    .split(" ")[2]
    .split("x")
]

if orig_dims[0] > orig_dims[1]:
    min_dim = orig_dims[1]
else:
    min_dim = orig_dims[0]

BASE_SCALING_FACTORS = (1, 2, 4, 8, 16, 32, 64, 128, 256)
SCALING_FACTORS = [sf for sf in BASE_SCALING_FACTORS if sf < ceil(min_dim / BASE_TILE)]

DOWNSIZING_FACTORS = []
p = 2
cont = True
while cont:
    DOWNSIZING_FACTORS.append(p)
    cont = (floor(min_dim / pow(2, p))) > 1
    p = p + 1


im_calls = []
for sf in SCALING_FACTORS:
    source_w = floor(orig_dims[0] / sf)
    source_h = ceil(orig_dims[1] / sf)
    im_calls.append(
        f'convert {SOURCE_IMAGE} -monitor -adaptive-resize {source_w}x{source_h} -crop {BASE_TILE}x{BASE_TILE} -set filename:tile "%[fx:page.x],%[fx:page.y],%[fx:w],%[fx:h]" +repage +adjoin "{OUTPUT_DIR}/{BASE_TILE},{sf},%[filename:tile].jpg"'
    )

for call in tqdm(im_calls, desc="Creating tiles"):
    code = os.system(call)

image_results = []

for f in glob(OUTPUT_DIR + "/*.jpg"):
    attrs = [int(i) for i in os.path.basename(f).split(".")[0].split(",")]
    image_results.append(
        {
            "filename": f,
            "attributes": {
                "base": attrs[0],
                "scaling_factor": attrs[1],
                "x": attrs[2],
                "y": attrs[3],
                "w": attrs[4],
                "h": attrs[5],
            },
        }
    )

for i in tqdm(image_results, desc="Full tiles"):
    attrs = i["attributes"]
    sf = attrs["scaling_factor"]
    real_x = attrs["x"] * sf
    real_y = attrs["y"] * sf
    real_w = attrs["w"] * sf
    real_h = attrs["h"] * sf
    target_dir = f"{OUTPUT_DIR}/{real_x},{real_y},{real_w},{real_h}/{attrs['w']},/0"
    os.makedirs(target_dir)
    os.rename(i["filename"], target_dir + "/default.jpg")

downsize_calls = []
for df in DOWNSIZING_FACTORS:
    new_w = ceil(orig_dims[0] * 1 / pow(2, df))
    new_h = ceil(orig_dims[1] * 1 / pow(2, df))
    downsize_calls.append(
        f"convert {SOURCE_IMAGE} -adaptive-resize {new_w}x{new_h} {OUTPUT_DIR}/{new_w},{new_h}.jpg"
    )

for call in tqdm(downsize_calls, desc="Downsizing"):
    code = os.system(call)

full_results = glob(OUTPUT_DIR + "/*.jpg")

full_dims = []

for i in full_results:
    components = os.path.basename(i).split(".")[0].split(",")
    target_dir = f"{OUTPUT_DIR}/full/{components[0]},/0"
    os.makedirs(target_dir)
    os.rename(i, target_dir + "/default.jpg")
    full_dims.append({"width": int(components[0]), "height": "full"})


manifest = {
    "@context": "http://iiif.io/api/image/2/context.json",
    "@id": os.path.basename(SOURCE_IMAGE).split(".")[0],
    "profile": [
        "http://iiif.io/api/image/2/level0.json",
        {"formats": ["jpg"], "qualities": ["default"]},
    ],
    "protocol": "http://iiif.io/api/image",
    "sizes": full_dims,
    "tiles": [
        {"height": BASE_TILE, "scaleFactors": SCALING_FACTORS, "width": BASE_TILE}
    ],
    "width": orig_dims[0],
    "height": orig_dims[1],
}

json.dump(manifest, open(f"{OUTPUT_DIR}/info.json", "w"), indent=2)

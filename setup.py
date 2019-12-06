import sys
import shutil
import setuptools

version = "0.0.2"

with open("README.md") as f:
    long_description = f.read()

if shutil.which("convert") is None:
    sys.exit("Please install ImageMagick, and make sure it is in your system path.")

setuptools.setup(
    name="magick_tile",
    version=version,
    url="https://github.com/cmu-lib/magick_tile/",
    author="Matthew Lincoln",
    author_email="matthew.d.lincoln@gmail.com",
    license="MIT",
    py_modules=["magick_tile"],
    description="Write iiif-image tiles using ImageMagick",
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=["tqdm"],
    python_requires=">=3.*",
    entry_points={"console_scripts": ["magick_tile=magick_tile:main"]},
)

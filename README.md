# pyHIS

pyHIS is a Python library and CLI tool for reading HIS files and converting them to sequential TIFF images.

## Features
- Read HIS format files and extract image data and comments
- Export images as TIFF files with metadata
- Command-line interface for batch conversion

## Usage
```
python his2tiff.py input.his output_dir --prefix img
```
This will convert all images in `input.his` to TIFF files in `output_dir` with filenames like `img0000.tiff`, `img0001.tiff`, etc.
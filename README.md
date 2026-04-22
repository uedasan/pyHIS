# [pyHIS](https://github.com/uedasan/pyHIS)

pyHIS is a Python library and CLI tool for reading HIS files and converting them to sequential TIFF images.

Current version: `0.2.1`

## Features
- Read HIS format files and extract image data and comments
- Export images as TIFF files with metadata
- Command-line interface for batch conversion
- `HISFile`: safe reader that returns copied NumPy arrays
- `FastHISFile`: zero-copy reader via `mmap` for high-throughput reads

## Setup
```bash
uv sync
```

## Usage
```
uv run his2tiff input.his output_dir --prefix img
```
This will convert all images in `input.his` to TIFF files in `output_dir` with filenames like `img0000.tiff`, `img0001.tiff`, etc.

If `output_dir` is omitted, `his2tiff` creates a `tiff` folder next to the input `.his` file. This is also the default behavior when dropping a `.his` file onto `his2tiff.exe` on Windows.

## Build Exe
```bash
uv run pyinstaller his2tiff.spec
```

## Compatibility Note
`HISFile` now prioritizes safe Python usage over raw read speed.

- `HISFile.read_image()` and `HISFile.read_line()` return copied NumPy arrays.
- `HISFile` supports `with`.
- Code that relied on zero-copy arrays from `HISFile` should switch to `FastHISFile`.

## Python API
Safe usage:

```python
from pyHIS import HISFile

with HISFile("input.his") as his:
    image, comment = his.read_image(0, return_comment=True)
```

High-throughput usage:

```python
from pyHIS import FastHISFile

his = FastHISFile("input.his")
image, comment = his.read_image(0, return_comment=True)
his.close()
```

`FastHISFile` returns zero-copy NumPy views into the memory-mapped file.
Keep the `FastHISFile` instance open while using returned arrays, and do not
call `close()` while those arrays are still referenced.

## Release file
A Windows executable (.exe) is available at the [Releases](https://github.com/uedasan/pyHIS/releases) page.


import argparse
from pathlib import Path
from pyHIS import FastHISFile
import tifffile
from tqdm import trange

def main():

    parser = argparse.ArgumentParser(description="Convert HIS file to sequential TIFF images.")
    parser.add_argument("his_file", help="Path to input HIS file.")
    parser.add_argument("output_dir", nargs="?", help="Directory to save output TIFF files. (default: tiff next to input HIS file)")
    parser.add_argument("--prefix", default="img", help="Prefix for output file names (default: img)")
    args = parser.parse_args()

    his_path = Path(args.his_file)
    output_dir = Path(args.output_dir) if args.output_dir else his_path.parent / "tiff"
    output_dir.mkdir(parents=True, exist_ok=True)
    his = FastHISFile(str(his_path))
    image = None
    try:
        for i in trange(len(his)):
            image, comment = his.read_image(i, return_comment=True)
            out_path = output_dir / f"{args.prefix}{i:04d}.tiff"
            tifffile.imwrite(out_path, image, imagej=True, metadata={"Info": comment})
            image = None
    finally:
        image = None
        his.close()


if __name__ == "__main__":
    main()

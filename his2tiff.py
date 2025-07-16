
import argparse
import os
from pyHIS import HISFile
import tifffile
from tqdm import trange

def main():

    parser = argparse.ArgumentParser(description="Convert HIS file to sequential TIFF images.")
    parser.add_argument("his_file", help="Path to input HIS file.")
    parser.add_argument("output_dir", nargs="?", default="tiff", help="Directory to save output TIFF files. (default: tiff)")
    parser.add_argument("--prefix", default="img", help="Prefix for output file names (default: img)")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    his = HISFile(args.his_file)
    for i in trange(len(his)):
        image, comment = his.read_image(i, return_comment=True)
        out_path = os.path.join(args.output_dir, f"{args.prefix}{i:04d}.tiff")
        tifffile.imwrite(out_path, image, imagej=True, metadata={"Info": comment})


if __name__ == "__main__":
    main()

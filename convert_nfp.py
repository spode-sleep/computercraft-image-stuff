#!/usr/bin/python
# -*- coding: utf-8 -*-
from PIL import Image
import nfp
import argparse
import os
import shutil

# default resize width/height when converting image -> nfp
DEFAULT_WIDTH, DEFAULT_HEIGHT = 164, 81

desc = (
    "Convert standard image files to ComputerCraft nfp files, and vice "
    "versa. Input file type is identified by extension (.nfp, .jpg, etc.), "
    "and output files use the input filename with a new extension."
)
files_help = "input files, nfp or image (must have correct file extension)"
nfp_desc = "optional arguments when converting image -> nfp"
skip_help = "skip default behavior of resizing image before conversion"
width_help = "if resizing, new width (default: {})".format(DEFAULT_WIDTH)
height_help = "if resizing, new height (default: {})".format(DEFAULT_HEIGHT)
im_desc = "optional arguments when converting nfp -> image"
format_help = (
    "output format passed to Image.save() (also output file extension "
    "unless -e argument specified), see PIL docs for supported formats, "
    "default: PNG"
)
ext_help = (
    "if specified, will be used as the output file extension instead of "
    "FORMAT"
)
rm_help = "remove the original image after converting"
dither_help = "enables dithering"
folder_processing_help = ("Enables processing of whole folder. "
    "The program will recursively process every file of the specified input extension in the input folder. "
    "Put path to the input folder in --folder-processing-input-folder-path argument. "
    "Put path to the output folder in --folder-processing-output-folder-path argument. "
    "Put input extension in --folder-processing-input-extension argument. "
    "Put output extension in --extension/--f_format argument. "
)
folder_processing_input_folder_path_help = "Sets input folder path in folder processing."
folder_processing_output_folder_path_help = "Sets output folder path in folder processing."
folder_processing_input_extension_help = "Sets input extension in folder processing.  For example, \".png\" without quotes."

parser = argparse.ArgumentParser(description=desc)
parser.add_argument("files", nargs='*', help=files_help)
nfp_group = parser.add_argument_group("nfp arguments", description=nfp_desc)
nfp_group.add_argument("--skip-resize", "-s", help=skip_help,
                       action="store_true", default=False)
nfp_group.add_argument("--resize-width", "-w", help=width_help,
                       metavar="WIDTH", type=int, default=DEFAULT_WIDTH)
nfp_group.add_argument("--resize-height", "-H", help=height_help,
                       metavar="HEIGHT", type=int, default=DEFAULT_HEIGHT)
im_group = parser.add_argument_group("image arguments", description=im_desc)
im_group.add_argument("--format", "-f", help=format_help, metavar="FORMAT",
                      dest="f_format", default="PNG")
im_group.add_argument("--extension", "-e", help=ext_help)
im_group.add_argument("--remove", "-r", help=rm_help, action="store_true")
im_group.add_argument("--dither", "-d", help=dither_help, action="store_true")
im_group.add_argument("--folder-processing", "-fp", help=folder_processing_help, action="store_true")
im_group.add_argument("--folder-processing-input-folder-path", "-fpif", help=folder_processing_input_folder_path_help)
im_group.add_argument("--folder-processing-output-folder-path", "-fpof", help=folder_processing_output_folder_path_help)
im_group.add_argument("--folder-processing-input-extension", "-fpie", help=folder_processing_input_extension_help)

args = parser.parse_args()

def recursively_find_files_by_extension(input_folder, extension):
    matches = []
    for root, _, files in os.walk(input_folder):
        for file in files:
            if file.endswith(extension):
                matches.append(os.path.join(root, file))
    return matches

def recreate_folder_structure(input_folder, output_folder, file_paths):
    for file_path in file_paths:
        relative_path = os.path.relpath(file_path, input_folder)
        new_folder = os.path.join(output_folder, relative_path)
        
        os.makedirs(os.path.dirname(new_folder), exist_ok=True)


def get_output_paths(input_folder, output_folder, target_extension, file_paths):
    new_paths = []
    
    for file_path in file_paths:
        relative_path = os.path.relpath(file_path, input_folder)
        new_path = os.path.join(output_folder, os.path.splitext(relative_path)[0] + target_extension)
        new_paths.append(new_path)
        
    return new_paths

files = []
new_files_paths = []
if args.folder_processing:
    input_folder = args.folder_processing_input_folder_path
    output_folder = args.folder_processing_output_folder_path
    input_extension = args.folder_processing_input_extension
    output_extension = args.extension if args.extension else "." + args.format

    if not (args.extension or args.format) or not output_extension or not output_folder or not input_folder:
        raise Exception("No input/output extension or input/output path")
    files = recursively_find_files_by_extension(input_folder, input_extension)
    recreate_folder_structure(input_folder, output_folder, files)
    new_files_paths = get_output_paths(input_folder, output_folder, output_extension, files)
else:
    files = args.files

for i, file in enumerate(files):
    filename, ext = os.path.splitext(file)
    if not ext:
        parser.error("filename must have appropriate extension")
    if ext.upper() == ".NFP":
        with open(file, "rt") as f:
            nfp_file = f.read()
        im = nfp.nfp_to_img(nfp_file)
        new_ext = args.f_format.replace(" ", "").lower()
        if args.extension:
            new_ext = args.extension
        if args.folder_processing:
            im.save(new_files_paths[i], args.f_format)
        else:
            im.save("{}.{}".format(filename, new_ext), args.f_format)
    else:
        im = Image.open(file)
        if args.skip_resize:
            nfp_file = nfp.img_to_nfp(im, dither=1 if args.dither else 0)
        else:
            nfp_file = nfp.img_to_nfp(
                im,
                (args.resize_width, args.resize_height),
                dither=1 if args.dither else 0
            )
        if args.folder_processing:
            with open(new_files_paths[i], "wt") as f:
                f.write(nfp_file)
        else:
            with open("{}.nfp".format(filename), "wt") as f:
                f.write(nfp_file)
    if args.remove:
        os.remove(file)

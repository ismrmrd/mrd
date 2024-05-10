#!/usr/bin/env bash

set -e

PATH="../cpp/build:$PATH"
export PYTHONPATH="../python:$PYTHONPATH"
export MATLABPATH="../matlab/toolbox:../matlab/toolbox/examples:$MATLABPATH"

echo Generating Phantoms
mrd_phantom > phantom.cpp.bin
python -m mrd.tools.phantom > phantom.py.bin
./matlab_generate_phantom.sh > phantom.mat.bin


echo Reconstructing C++ Phantom
cat phantom.cpp.bin | mrd_stream_recon > cpp2cpp_images.bin
cat phantom.cpp.bin | python -m mrd.tools.stream_recon > cpp2py_images.bin
cat phantom.cpp.bin | ./matlab_stream_recon.sh > cpp2mat_images.bin

echo Reconstructing Python Phantom
cat phantom.py.bin | mrd_stream_recon > py2cpp_images.bin
cat phantom.py.bin | python -m mrd.tools.stream_recon  > py2py_images.bin
cat phantom.py.bin | ./matlab_stream_recon.sh > py2mat_images.bin

echo Reconstructing MATLAB Phantom
cat phantom.mat.bin | mrd_stream_recon > mat2cpp_images.bin
cat phantom.mat.bin | python -m mrd.tools.stream_recon > mat2py_images.bin
cat phantom.mat.bin | ./matlab_stream_recon.sh > mat2mat_images.bin


echo Verifying reconstructions
python verify_images.py cpp*images.bin
python verify_images.py py*images.bin
python verify_images.py mat*images.bin


echo Generate PNGs
cat cpp2cpp_images.bin  | mrd_image_stream_to_png cpp2cpp
cat py2py_images.bin    | python -m mrd.tools.export_png_images -o py2py
cat mat2mat_images.bin  | ./matlab_export_png_images.sh mat2mat


echo Cleaning up
rm -f ./*.bin ./*.png

#!/usr/bin/env bash

set -e

PATH="../cpp/build:$PATH"
export PYTHONPATH="../python:$PYTHONPATH"
export MATLABPATH="../matlab/toolbox:../matlab/toolbox/examples:$MATLABPATH"

function ifmatlab() {
  [[ -n "$MRD_MATLAB_ENABLED" ]]
}

echo Generating Phantoms
mrd_phantom > phantom.cpp.bin
python -m mrd.tools.phantom > phantom.py.bin
ifmatlab && ./matlab_generate_phantom.sh > phantom.mat.bin

echo Reconstructing C++ Phantom
cat phantom.cpp.bin | mrd_stream_recon > cpp2cpp_images.bin
cat phantom.cpp.bin | python -m mrd.tools.stream_recon > cpp2py_images.bin
ifmatlab && cat phantom.cpp.bin | ./matlab_stream_recon.sh > cpp2mat_images.bin

echo Reconstructing Python Phantom
cat phantom.py.bin | mrd_stream_recon > py2cpp_images.bin
cat phantom.py.bin | python -m mrd.tools.stream_recon  > py2py_images.bin
ifmatlab && cat phantom.py.bin | ./matlab_stream_recon.sh > py2mat_images.bin

ifmatlab && echo Reconstructing MATLAB Phantom
ifmatlab && cat phantom.mat.bin | mrd_stream_recon > mat2cpp_images.bin
ifmatlab && cat phantom.mat.bin | python -m mrd.tools.stream_recon > mat2py_images.bin
ifmatlab && cat phantom.mat.bin | ./matlab_stream_recon.sh > mat2mat_images.bin


echo Verifying reconstructions
python verify_images.py cpp*images.bin
python verify_images.py py*images.bin
ifmatlab && python verify_images.py mat*images.bin


echo Generate PNGs
cat cpp2cpp_images.bin  | mrd_image_stream_to_png -o cpp2cpp
cat py2py_images.bin    | python -m mrd.tools.export_png_images -o py2py
ifmatlab && cat mat2mat_images.bin  | ./matlab_export_png_images.sh mat2mat


echo Testing again using named pipes
test -e recon_in.pipe || mkfifo recon_in.pipe
test -e recon_out.pipe || mkfifo recon_out.pipe

mrd_phantom --output recon_in.pipe &
mrd_stream_recon --input recon_in.pipe --output recon_out.pipe &
mrd_image_stream_to_png --input recon_out.pipe

python -m mrd.tools.phantom --output recon_in.pipe &
python -m mrd.tools.stream_recon --input recon_in.pipe --output recon_out.pipe &
python -m mrd.tools.export_png_images --input recon_out.pipe


echo Cleaning up
rm -f ./*.bin ./*.png ./*.pipe

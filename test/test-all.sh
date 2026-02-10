#!/usr/bin/env bash

set -eo pipefail

TESTDIR=$(dirname "$(realpath "$0")")
WORKSPACE=$(dirname "$TESTDIR")

export PATH="${WORKSPACE}/cpp/build:$PATH"
export PYTHONPATH="${WORKSPACE}/python:$PYTHONPATH"
export MATLABPATH="${WORKSPACE}/matlab/toolbox:${WORKSPACE}/matlab/toolbox/examples:$MATLABPATH"

function ifmatlab() {
  [[ -n "$MRD_MATLAB_ENABLED" ]]
}

function cleanup() {
  rm -f ./*.mrd ./*.png ./*.pipe
  popd >/dev/null
}

pushd "$TESTDIR" >/dev/null || exit 1
trap cleanup EXIT

echo Running end-to-end tests...

####
# Test basic reconstruction

generate_args=(--coils 14
      --matrix 72
      --repetitions 2
      --oversampling 3
      --noise-level 0.0
      --noise-calibration
      --store-coordinates
)

## Generate phantoms and save coil images for reference
# mrd_phantom "${generate_args[@]}" --output phantom.cpp.mrd --output-coils coil_images.cpp.mrd
python -m mrd.tools.phantom "${generate_args[@]}" --output phantom.py.mrd --output-coils coil_images.py.mrd
ifmatlab && run-matlab-command 'generate_phantom("phantom.mat.mrd", "ncoils", 14, "matrix_size", 72, "repetitions", 2, "oversampling", 3, "noise_level", 0, "noise_calibration", true, "store_coordinates", true, "output_coils", "coil_images.mat.mrd")'

# ## Reconstruct phantoms using each implementation
# mrd_stream_recon -i phantom.cpp.mrd -o reconstructed.cpp.cpp.mrd
# mrd_stream_recon -i phantom.py.mrd -o reconstructed.py.cpp.mrd
# ifmatlab && mrd_stream_recon -i phantom.mat.mrd -o reconstructed.mat.cpp.mrd
# python -m mrd.tools.stream_recon --input phantom.py.mrd --output reconstructed.py.py.mrd
# python -m mrd.tools.stream_recon --input phantom.cpp.mrd --output reconstructed.cpp.py.mrd
# ifmatlab && python -m mrd.tools.stream_recon --input phantom.mat.mrd --output reconstructed.mat.py.mrd
# ifmatlab && run-matlab-command 'stream_recon("phantom.mat.mrd", "reconstructed.mat.mat.mrd")'
# ifmatlab && run-matlab-command 'stream_recon("phantom.cpp.mrd", "reconstructed.cpp.mat.mrd")'
# ifmatlab && run-matlab-command 'stream_recon("phantom.py.mrd", "reconstructed.py.mat.mrd")'

# ## Compare reconstructions to reference coil images
# python "$TESTDIR"/validate_recon.py --reference coil_images.cpp.mrd --testdata reconstructed.cpp.cpp.mrd
# python "$TESTDIR"/validate_recon.py --reference coil_images.cpp.mrd --testdata reconstructed.cpp.py.mrd
# ifmatlab && python "$TESTDIR"/validate_recon.py --reference coil_images.cpp.mrd --testdata reconstructed.cpp.mat.mrd
# python "$TESTDIR"/validate_recon.py --reference coil_images.py.mrd --testdata reconstructed.py.cpp.mrd
# python "$TESTDIR"/validate_recon.py --reference coil_images.py.mrd --testdata reconstructed.py.py.mrd
# ifmatlab && python "$TESTDIR"/validate_recon.py --reference coil_images.py.mrd --testdata reconstructed.py.mat.mrd
# ifmatlab && python "$TESTDIR"/validate_recon.py --reference coil_images.mat.mrd --testdata reconstructed.mat.cpp.mrd
# ifmatlab && python "$TESTDIR"/validate_recon.py --reference coil_images.mat.mrd --testdata reconstructed.mat.py.mrd
# ifmatlab && python "$TESTDIR"/validate_recon.py --reference coil_images.mat.mrd --testdata reconstructed.mat.mat.mrd

# ####
# # Test that phantom generation (with parallel imaging) is consistent across implementations

# generate_args=(--coils 14
#       --matrix 72
#       --repetitions 2
#       --acceleration 2
#       --calibration-width 10
#       --noise-level 0.0
#       --noise-calibration
# )

# ## Generate phantoms and save coil images for reference
# mrd_phantom "${generate_args[@]}" --output phantom.cpp.mrd
# python -m mrd.tools.phantom "${generate_args[@]}" --output phantom.py.mrd
# ifmatlab && run-matlab-command 'generate_phantom("phantom.mat.mrd", "ncoils", 14, "matrix_size", 72, "repetitions", 2, "acceleration", 2, "calibration_width", 10, "noise_level", 0, "noise_calibration", true)'

# python "$TESTDIR"/compare_dataset.py phantom.cpp.mrd phantom.py.mrd
# ifmatlab && python "$TESTDIR"/compare_dataset.py phantom.cpp.mrd phantom.mat.mrd

# ####
# # Test cross-language compatibility using anonymous pipes

# ## Generate phantoms
# mrd_phantom > phantom.cpp.mrd
python -m mrd.tools.phantom > phantom.py.mrd
# ifmatlab && ./matlab_generate_phantom.sh > phantom.mat.mrd

# ## Reconstruct C++ phantom
# cat phantom.cpp.mrd | mrd_stream_recon > cpp2cpp_images.mrd
# cat phantom.cpp.mrd | python -m mrd.tools.stream_recon > cpp2py_images.mrd
# ifmatlab && cat phantom.cpp.mrd | ./matlab_stream_recon.sh > cpp2mat_images.mrd

# ## Reconstruct Python phantom
# cat phantom.py.mrd | mrd_stream_recon > py2cpp_images.mrd
cat phantom.py.mrd | python -m mrd.tools.stream_recon  > py2py_images.mrd
# ifmatlab && cat phantom.py.mrd | ./matlab_stream_recon.sh > py2mat_images.mrd

# ## Reconstruct MATLAB phantom
# ifmatlab && cat phantom.mat.mrd | mrd_stream_recon > mat2cpp_images.mrd
# ifmatlab && cat phantom.mat.mrd | python -m mrd.tools.stream_recon > mat2py_images.mrd
# ifmatlab && cat phantom.mat.mrd | ./matlab_stream_recon.sh > mat2mat_images.mrd

# ## Compare reconstructions
# python compare_images.py cpp*images.mrd
python compare_images.py py*images.mrd
# ifmatlab && python compare_images.py mat*images.mrd

# ## Generate PNGs
# cat cpp2cpp_images.mrd  | mrd_image_stream_to_png -o cpp2cpp
# cat py2py_images.mrd    | python -m mrd.tools.export_png_images -o py2py
# ifmatlab && cat mat2mat_images.mrd  | ./matlab_export_png_images.sh mat2mat

# ####
# # Test again using named pipes
# test -e recon_in.pipe || mkfifo recon_in.pipe
# test -e recon_out.pipe || mkfifo recon_out.pipe

# mrd_phantom --output recon_in.pipe &
# mrd_stream_recon --input recon_in.pipe --output recon_out.pipe &
# mrd_image_stream_to_png --input recon_out.pipe

python -m mrd.tools.phantom --output recon_in.pipe &
python -m mrd.tools.stream_recon --input recon_in.pipe --output recon_out.pipe &
python -m mrd.tools.export_png_images --input recon_out.pipe

# # TODO: Add named pipe test for MATLAB
# # ifmatlab && run-matlab-command 'generate_phantom("recon_in.pipe")' &
# # ifmatlab && run-matlab-command 'stream_recon("recon_in.pipe", "recon_out.pipe")' &
# # ifmatlab && run-matlab-command 'export_png_images("recon_out.pipe")' &

echo Finished end-to-end tests

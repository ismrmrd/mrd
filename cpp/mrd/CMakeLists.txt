include_directories(../)

find_package(ISMRMRD 1.13.4 REQUIRED)

add_executable(
  mrd_phantom
  mrd_phantom.cc
  shepp_logan_phantom.cc
  )

target_link_libraries(
  mrd_phantom
  mrd_generated
  fftw3f
)

add_executable(
  mrd_hdf5_to_stream
  mrd_hdf5_to_stream.cc
)

  target_link_libraries(
  mrd_hdf5_to_stream
  mrd_generated
)

add_executable(
  mrd_stream_to_hdf5
  mrd_stream_to_hdf5.cc
)

  target_link_libraries(
  mrd_stream_to_hdf5
  mrd_generated
)

add_executable(
  mrd_stream_recon
  mrd_stream_recon.cc
)

target_link_libraries(
    mrd_stream_recon
    fftw3f
    mrd_generated
)

add_executable(
  ismrmrd_to_mrd
  ismrmrd_to_mrd.cc
)

target_link_libraries(
  ismrmrd_to_mrd
  mrd_generated
  ISMRMRD::ISMRMRD
)

find_package(ImageMagick COMPONENTS Magick++ REQUIRED)
find_package(fmt REQUIRED)
include_directories(${ImageMagick_INCLUDE_DIRS})

add_executable(
  mrd_image_stream_to_png
  mrd_image_stream_to_png.cc
)

target_compile_options(mrd_image_stream_to_png PRIVATE "-DMAGICKCORE_QUANTUM_DEPTH=8" "-DMAGICKCORE_HDRI_ENABLE=0")
target_link_libraries(
  mrd_image_stream_to_png
  mrd_generated
  ${ImageMagick_LIBRARIES}
  fmt::fmt
)

add_executable(
  mrd_to_ismrmrd
  mrd_to_ismrmrd.cc
)

target_link_libraries(
  mrd_to_ismrmrd
  mrd_generated
  ISMRMRD::ISMRMRD
)

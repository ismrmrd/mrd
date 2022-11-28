include_directories(../)

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

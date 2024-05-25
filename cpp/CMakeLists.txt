cmake_minimum_required(VERSION 3.19)
project(mrd)

set(MRD_VERSION_STRING $ENV{MRD_VERSION_STRING})
message(STATUS "MRD_VERSION_STRING: ${MRD_VERSION_STRING}")

SET(CMAKE_CXX_FLAGS_DEBUG "-O0 -g")
SET(CMAKE_C_FLAGS_DEBUG "-O0 -g")

#Set the build type to Release if not specified
if (NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release CACHE STRING
            "Choose the type of build, options are: None Debug Release RelWithDebInfo MinSizeRel."
            FORCE)
endif ()

if(NOT CMAKE_CXX_STANDARD)
    set(CMAKE_CXX_STANDARD 17)
endif()

set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR})
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY  ${CMAKE_BINARY_DIR})

add_compile_options(-Wall -Wextra -pedantic -Werror)
add_subdirectory(mrd)
add_subdirectory(mrd-tools)

add_executable(mrd_minimal_example minimal_example.cc)
target_link_libraries(mrd_minimal_example mrd_generated)

install(DIRECTORY mrd DESTINATION include COMPONENT Devel)
install(TARGETS mrd_generated DESTINATION lib)
install(TARGETS
    ismrmrd_to_mrd
    mrd_hdf5_to_stream
    mrd_image_stream_to_png
    mrd_phantom
    mrd_stream_recon
    mrd_stream_to_hdf5
    mrd_to_ismrmrd
    mrd_minimal_example
    DESTINATION bin)

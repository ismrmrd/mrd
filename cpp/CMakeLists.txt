cmake_minimum_required(VERSION 3.19)
project(mrd)

set(MRD_VERSION_MAJOR 2)
set(MRD_VERSION_MINOR 0)
set(MRD_VERSION_PATCH 0-alpha.2)

set(MRD_VERSION_STRING ${MRD_VERSION_MAJOR}.${MRD_VERSION_MINOR}.${MRD_VERSION_PATCH})


SET(CMAKE_CXX_FLAGS_DEBUG "-O0")
SET(CMAKE_C_FLAGS_DEBUG "-O0")

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
add_subdirectory(generated)
add_subdirectory(mrd)

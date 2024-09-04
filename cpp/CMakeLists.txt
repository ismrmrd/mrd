cmake_minimum_required(VERSION 3.19)

file(STRINGS "../VERSION" MRD_VERSION_STRING)

project(mrd VERSION ${MRD_VERSION_STRING})

message(STATUS "MRD_VERSION_STRING: ${MRD_VERSION_STRING}")

SET(CMAKE_CXX_FLAGS_DEBUG "-O0 -g")
SET(CMAKE_C_FLAGS_DEBUG "-O0 -g")

#Set the build type to Release if not specified
if (NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release CACHE STRING
            "Choose the type of build, options are: None Debug Release RelWithDebInfo MinSizeRel."
            FORCE)
endif ()
message(STATUS "Build type: ${CMAKE_BUILD_TYPE}")

if(NOT CMAKE_CXX_STANDARD)
    set(CMAKE_CXX_STANDARD 17)
endif()

set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR})
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY  ${CMAKE_BINARY_DIR})

find_package(ISMRMRD 1.13.4 REQUIRED)

add_compile_options(-Wall -Wextra -pedantic -Werror)
add_subdirectory(mrd)
add_subdirectory(mrd-tools)

# Minimal example
add_executable(mrd_minimal_example minimal_example.cc)
target_link_libraries(mrd_minimal_example mrd_generated)
install(TARGETS mrd_minimal_example DESTINATION bin)


string(REGEX MATCH "[0-9]+" MRD_SOVERSION ${MRD_VERSION_STRING})
message(STATUS "MRD_SOVERSION: ${MRD_SOVERSION}")

# MRD Library (libmrd)
add_library(mrd SHARED $<TARGET_OBJECTS:mrd_generated> mrd/converters.cc)
add_library(mrd::mrd ALIAS mrd)

target_include_directories(mrd PUBLIC "$<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}>")

# MRD links with ISMRMRD only as long as we need to provide a conversion API
target_link_libraries(mrd PRIVATE mrd_generated PUBLIC ISMRMRD::ISMRMRD)
set_target_properties(mrd PROPERTIES
  VERSION ${MRD_VERSION_STRING}
  SOVERSION ${MRD_SOVERSION}
)

# Installation (libmrd)
include(GNUInstallDirs)
include(CMakePackageConfigHelpers)

install(TARGETS mrd EXPORT mrd-targets
        COMPONENT Devel
        INCLUDES DESTINATION "${CMAKE_INSTALL_INCLUDEDIR}"
)
install(DIRECTORY mrd
        TYPE INCLUDE
        COMPONENT Devel
        FILES_MATCHING PATTERN "*.h"
)

set(MRD_INSTALL_CMAKEDIR "${CMAKE_INSTALL_LIBDIR}/cmake/mrd" CACHE STRING "Path to MRD CMake files")

install(EXPORT mrd-targets
  FILE mrd-targets.cmake
  DESTINATION "${MRD_INSTALL_CMAKEDIR}"
  NAMESPACE mrd::
  COMPONENT Devel
)

write_basic_package_version_file(
  "${CMAKE_CURRENT_BINARY_DIR}/mrd-config-version.cmake"
  VERSION ${MRD_VERSION_STRING}
  COMPATIBILITY SameMajorVersion
)

install(
  FILES
    "${CMAKE_CURRENT_SOURCE_DIR}/cmake/mrd-config.cmake"
    "${CMAKE_CURRENT_BINARY_DIR}/mrd-config-version.cmake"
  DESTINATION "${MRD_INSTALL_CMAKEDIR}"
  COMPONENT Devel
)
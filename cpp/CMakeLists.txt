cmake_minimum_required(VERSION 3.19)
project(mrd)

set(MRD_VERSION_STRING $ENV{MRD_VERSION_STRING})
message(STATUS "MRD_VERSION_STRING: ${MRD_VERSION_STRING}")
string(REGEX MATCH "[0-9]+" MRD_SOVERSION ${MRD_VERSION_STRING})
message(STATUS "MRD_SOVERSION: ${MRD_SOVERSION}")

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

find_package(ISMRMRD 1.13.4 REQUIRED)

add_compile_options(-Wall -Wextra -pedantic -Werror)
add_subdirectory(mrd)
add_subdirectory(mrd-tools)

# Minimal example
add_executable(mrd_minimal_example minimal_example.cc)
target_link_libraries(mrd_minimal_example mrd_generated)
install(TARGETS mrd_minimal_example DESTINATION bin)

# MRD Library (libmrd)
add_library(mrd SHARED $<TARGET_OBJECTS:mrd_generated> mrd/converters.cc)
# MRD links with ISMRMRD only as long as we need to provide a conversion API
target_link_libraries(mrd PRIVATE mrd_generated PUBLIC ISMRMRD::ISMRMRD)
set_target_properties(mrd PROPERTIES
  VERSION ${MRD_VERSION_STRING}
  SOVERSION ${MRD_SOVERSION}
  EXPORT_NAME MRD
)
install(TARGETS mrd
        EXPORT MRDTargets
        DESTINATION lib
        INCLUDES DESTINATION include
)
install(DIRECTORY mrd
        DESTINATION include
        COMPONENT Devel
        FILES_MATCHING PATTERN "*.h"
)

include(CMakePackageConfigHelpers)
write_basic_package_version_file(
  "${CMAKE_CURRENT_BINARY_DIR}/mrd/MRDConfigVersion.cmake"
  VERSION ${MRD_VERSION_STRING}
  COMPATIBILITY AnyNewerVersion
)

export(EXPORT MRDTargets
  FILE "${CMAKE_CURRENT_BINARY_DIR}/mrd/MRDTargets.cmake"
  NAMESPACE MRD::
)
configure_file(cmake/MRDConfig.cmake
  "${CMAKE_CURRENT_BINARY_DIR}/mrd/MRDConfig.cmake"
  COPYONLY
)

set(ConfigPackageLocation lib/cmake/mrd)
install(EXPORT MRDTargets
  FILE
    MRDTargets.cmake
  NAMESPACE
    MRD::
  DESTINATION
    ${ConfigPackageLocation}
)
install(
  FILES
    cmake/MRDConfig.cmake
    "${CMAKE_CURRENT_BINARY_DIR}/mrd/MRDConfigVersion.cmake"
  DESTINATION
    ${ConfigPackageLocation}
  COMPONENT
    Devel
)
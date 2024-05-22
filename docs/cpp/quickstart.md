# Quick Start

## Install

### Anaconda

We recommend using the `mrd` Anaconda package, which can be installed using `conda` or `mamba`:

```bash
$ mamba install ismrmrd:mrd
```

### CMake

If you use CMake, you can include MRD within your C++ project using CMake's `FetchContent` feature.
CMake will download and include the SDK directly from Github.

In your project CMakeLists.txt, declare a dependency on MRD one of two ways:

1. Using the full MRD repository by specifying either a git tag or commit hash
```cmake
FetchContent_Declare(
    mrd
    GIT_REPOSITORY https://github.com/ismrmrd/mrd.git
    GIT_TAG {tag -or- commit hash}
    SOURCE_SUBDIR cpp
    FIND_PACKAGE_ARGS
)
```

2. Using only the C++ source code for a given MRD release (smaller download, fewer files)
```cmake
FetchContent_Declare(
    mrd
    URL https://github.com/ismrmrd/mrd/releases/download/{tag}/mrd-cmake-src.tar.gz
)
```

Then, tell CMake to fetch the mrd source, include its headers, and link with the mrd library:

```cmake
FetchContent_MakeAvailable(mrd)

include_directories("${mrd_SOURCE_DIR}")

add_executable(myrecon main.cpp)
target_link_libraries(myrecon PRIVATE mrd_generated)
```

### Dependencies

The MRD source code is generated using yardl and requires the dependencies listed [here](https://microsoft.github.io/yardl/cpp/installation.html#c-dependencies).

These dependencies are automatically installed by the `mrd` conda package.

## Reading and Writing MRD streams

To read and write MRD streams, start with the following example:

<<< @/../cpp/minimal_example.cc{c++}

## Examples

See `cpp/mrd-tools` and `cpp/mrd-tools/CMakeLists.txt` in the MRD repository for example programs using the MRD library.

These tools are also installed as command-line executables when `mrd` is installed from Anaconda.

For example, to generate a cartesian Shepp-Logan phantom:

```bash
$ mrd_phantom --coils 8 --matrix 256 --repetitions 2 --oversampling 2 > phantom.bin
```

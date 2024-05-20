(FileFormat)=
# MRD File Format

MRD data can be stored and streamed in various formats, including raw binary, HDF5, and NDJSON.

We use [Yardl](https://microsoft.github.io/yardl/) to generate C++, Python, and MATLAB code for reading and writing MRD streams.

## Binary

The `mrd` binary format is the primary format for streaming raw MR data.

See also: [Yardl Binary Encoding Reference](https://microsoft.github.io/yardl/reference/binary.html)

Binary `mrd` streams can be read and written using C++, Python, and/or MATLAB.


## HDF5

[HDF5](https://www.hdfgroup.org/solutions/hdf5) format is commonly used due to its good compatibility across programming languages and platforms.  HDF5 is a hierarchical data format (much like a file system), which can contain multiple variable organized in groups (like folders in a file system). The variables can contain arrays of data values, custom defined structs, or simple text fields.  Interface libraries are provided for C++, Python, and MATLAB to simplify usage.  MRD HDF5 files can also be opened using standard HDF tools such as [HDFView](https://www.hdfgroup.org/downloads/hdfview/) or HDF5 packages such as [h5py](https://www.h5py.org/) for Python or the built-in [h5read](https://www.mathworks.com/help/matlab/ref/h5read.html) and associated functions in MATLAB.

An MRD HDF5 file has the following layout:
```
/                        Group
/Mrd                     Group
/Mrd/$yardl_schema       Dataset {SCALAR}
/Mrd/data                Group
/Mrd/data/$index         Dataset {1/Inf}
/Mrd/data/Acquisition    Dataset {0/Inf}
/Mrd/data/ImageComplexDouble Dataset {0/Inf}
/Mrd/data/ImageComplexFloat Dataset {0/Inf}
/Mrd/data/ImageDouble    Dataset {0/Inf}
/Mrd/data/ImageFloat     Dataset {1/Inf}
/Mrd/data/ImageInt       Dataset {0/Inf}
/Mrd/data/ImageInt16     Dataset {0/Inf}
/Mrd/data/ImageUint      Dataset {0/Inf}
/Mrd/data/ImageUint16    Dataset {0/Inf}
/Mrd/data/WaveformUint32 Dataset {0/Inf}
/Mrd/header              Dataset {SCALAR}
```

where `/Mrd/data` and `/Mrd/header` directly correspond to the `Header` and `StreamItem` elements of the top-level [MRD Protocol](../model/mrd_protocol.yml).

Only the C++ SDK provides an API for reading and writing HDF5 MRD streams


## NDJSON

The NDJSON serialization format is great for debugging and interoperability with other tools (like jq) but is it orders of magnitude less efficient than the binary or HDF5 formats.

The C++ and Python SDKs are both capable of reading and writing NDJSON.

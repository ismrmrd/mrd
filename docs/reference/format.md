# MRD Streaming Format

MRD data can be stored and streamed in binary format or as NDJSON.

MRD uses [Yardl](https://microsoft.github.io/yardl/) to generate C++, Python, and MATLAB code for reading and writing MRD streams.

## Binary

The MRD binary format is the primary format for streaming raw MR data.

Examples of reading and writing MRD streams are provided in the MRD repository:
- C++:
    - `cpp/mrd-tools/mrd_phantom.cc`
    - `cpp/mrd-tools/mrd_stream_recon.cc`
    - `cpp/mrd-tools/mrd_image_stream_to_png.cc`
- Python:
    - `python/mrd/tools/phantom.py`
    - `python/mrd/tools/stream_recon.py`
    - `python/mrd/tools/export_png_images.py`
- MATLAB:
    - `matlab/toolbox/examples/generate_phantom.m`
    - `matlab/toolbox/examples/stream_recon.m`
    - `matlab/toolbox/examples/export_png_images.m`

See also:
- Quick Start Guides for [Python](python/quickstart), [C++](cpp/quickstart), and [MATLAB](matlab/quickstart)
- [Yardl Binary Encoding Reference](https://microsoft.github.io/yardl/reference/binary.html)

## NDJSON

The NDJSON serialization format is great for debugging and interoperability with other tools (like jq) but is it orders of magnitude less efficient than the binary format.

The C++ and Python SDKs are both capable of reading and writing NDJSON.

To use MRD NDJSON readers/writers, substitute `ndjson` for `binary` in the constructor.
For example, in Python

```python
import mrd

header = mrd.Header()

with mrd.BinaryMrdWriter("phantom.bin") as w:    // [!code --]
with mrd.NDJsonMrdWriter("phantom.bin") as w:    // [!code ++]
    w.write_header(h)
    w.write_data(generate_data())
```

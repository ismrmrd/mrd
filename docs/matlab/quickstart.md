# Quick Start

## Install

The MRD MATLAB toolbox requires MATLAB R2022b or newer.

See [MRD Github Releases](https://github.com/ismrmrd/mrd/releases) for the most recent version of the MRD MATLAB Toolbox.

Download the `*.mltbx` file and double-click on it from *within the MATLAB Current Folder browser* to install it.

## Reading and Writing MRD Streams

To read and write MRD streams, start with the following example:

<<< @/../matlab/toolbox/examples/minimal_example.m{matlab}

## Examples

See `matlab/toolbox/examples` in the MRD repository for example MATLAB program using the MRD toolbox.

For example, to generate a cartesian Shepp-Logan phantom:

```matlab
>> cd matlab/toolbox/examples
>> addpath("../");
>> generate_phantom("test.bin", matrix_size=256, ncoils=8);
```

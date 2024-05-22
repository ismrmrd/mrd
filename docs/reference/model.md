# MRD Model

The Magnetic Resonance Data (MRD) format is a vendor neutral standard for describing data from MR acquisitions and reconstructions.

MRD version 2 and above uses [Yardl](https://microsoft.github.io/yardl/) to generate stream-oriented SDKs implementing the standard. MRD streaming formats are described [here](format).

The Model Definitions below are described using the [Yardl language](https://microsoft.github.io/yardl/cpp/language.html), and can be found in the `model/` subdirectory of the MRD repository.


## MRD Protocol

### Overview
The MRD Protocol describes an MRD stream or file, which contains:

1.  The [MRD header](#mrd-header) containing general metadata describing the acquisition, including MR system details and k-space sampling.
2.  A sequence of MRD datatypes that may be one of:
    1.  [Raw k-space data](#mrd-acquisition), stored as individual readout acquisitions.
    2.  [Image data](#mrd-image), stored as sets of 2D or 3D arrays.
    3.  [Waveforms](#mrd-waveform), storing physiological data such as electrocardiograms, pulse oximetry, or external triggering sources.

### Protocol Definitions
<<< @/../model/mrd_protocol.yml


## MRD Header

### Overview
The MRD Header contains general metadata describing the acquisition, including MR system details and k-space sampling.

The header contains a small set of mandatory parameters common to all MR acquisitions, but is extensible to parameters for specialized acquisitions such as b-values, venc, magnetization preparation durations, etc.

The most critical elements for image reconstruction are contained in the `encoding` field of the header, which describes the encoded spaced as well as the target reconstructed space.
This section allows reconstruction software to determine matrix sizes, oversampling factors, partial Fourier, etc.
An experiment can have multiple encoding spaces and it is possible to indicate on each acquired data readout, which encoding space the data belongs to (see the `encodingSpaceRef` field in [MRD Acquisition](#mrd-acquisition)).

### Header Definitions
<<< @/../model/mrd_header.yml


## MRD Acquisition

### Overview
Raw k-space data is stored as individual readout Acquisitions.
Each readout contains the complex raw data for all channels, a fixed header for metadata including encoding loop counters, and optionally corresponding k-space trajectory information.
Most datasets will be comprised of many acquisitions, each stored individually with its own header, optional trajectory, and raw data.

<style>
 .smalltable td {
   font-size:       80%;
   border-collapse: collapse;
   border-spacing:  0;
   border-width:    0;
   padding:         3px;
   border:          1px solid lightgray
 }
</style>

MR acquisition raw data are stored as complex valued floats, with dimensions `[coils, samples]`.
Data from all receiver channels are included in a single readout object.

Data is organized by looping through real/imaginary data, samples, then channels:

<table class="smalltable">
  <tr>
    <td style="text-align: center" colspan="6">Channel 1</td>
    <td style="text-align: center" colspan="6">Channel 2</td>
    <td style="text-align: center" rowspan="3">...</td>
    <td style="text-align: center" colspan="6">Channel n</td>
  </tr>
  <tr>
    <td style="text-align: center" colspan="2">Sample 1</td>
    <td style="text-align: center" colspan="2">...</td>
    <td style="text-align: center" colspan="2">Sample n</td>
    <td style="text-align: center" colspan="2">Sample 1</td>
    <td style="text-align: center" colspan="2">...</td>
    <td style="text-align: center" colspan="2">Sample n</td>
    <td style="text-align: center" colspan="2">Sample 1</td>
    <td style="text-align: center" colspan="2">...</td>
    <td style="text-align: center" colspan="2">Sample n</td>
  </tr>
  <tr>
    <td style="text-align: center">Re</td> <td style="text-align: center">Im</td>
    <td style="text-align: center">Re</td> <td style="text-align: center">Im</td>
    <td style="text-align: center">Re</td> <td style="text-align: center">Im</td>
    <td style="text-align: center">Re</td> <td style="text-align: center">Im</td>
    <td style="text-align: center">Re</td> <td style="text-align: center">Im</td>
    <td style="text-align: center">Re</td> <td style="text-align: center">Im</td>
    <td style="text-align: center">Re</td> <td style="text-align: center">Im</td>
    <td style="text-align: center">Re</td> <td style="text-align: center">Im</td>
    <td style="text-align: center">Re</td> <td style="text-align: center">Im</td>
  </tr>
</table>

k-space trajectory information is optionally included with each readout as a `float32` array with dimensions `[basis, samples]`.

Trajectory data is organized by looping through the dimensions first then the samples:

<table class="smalltable">
    <tr>
    <td style="text-align: center" colspan="2">Sample 1</td>
    <td style="text-align: center" colspan="2">Sample 2</td>
    <td style="text-align: center" rowspan="2">...</td>
    <td style="text-align: center" colspan="2">Sample n</td>
    </tr>
    <tr>
    <td style="text-align: center">k<sub>x</sub></td>
    <td style="text-align: center">k<sub>y</sub></td>
    <td style="text-align: center">k<sub>x</sub></td>
    <td style="text-align: center">k<sub>y</sub></td>
    <td style="text-align: center">k<sub>x</sub></td>
    <td style="text-align: center">k<sub>y</sub></td>
    </tr>
</table>

### Acquisition Definitions
<<< @/../model/mrd_acquisition.yml


## MRD Image

### Overview
Image data is stored as either sets of 2D or 3D arrays with a fixed Image header of common properties and metadata.
Images can be organized into series of common types and multi-channel data is supported for non-coil-combined images.

Image data is organized as a 4-D array of the chosen image data type with dimensions `[channel, z, y, x]`.

For example, 2D image data would be formatted as:
<style>
 .smalltable td {
   font-size:       80%;
   border-collapse: collapse;
   border-spacing:  0;
   border-width:    0;
   padding:         3px;
   border:          1px solid lightgray
 }
</style>

<table class="smalltable">
  <tr>
    <td style="text-align: center" colspan="9">Channel 1</td>
    <td style="text-align: center" rowspan="3">...</td>
    <td style="text-align: center" colspan="9">Channel n</td>
  </tr>
  <tr>
    <td style="text-align: center" colspan="3">y<sub>1</sub></td>
    <td style="text-align: center" colspan="3">...</td>
    <td style="text-align: center" colspan="3">y<sub>n</sub></td>
    <td style="text-align: center" colspan="3">y<sub>1</sub></td>
    <td style="text-align: center" colspan="3">...</td>
    <td style="text-align: center" colspan="3">y<sub>n</sub></td>
  </tr>
  <tr>
    <td style="text-align: center">x<sub>1</sub></td>
    <td style="text-align: center">...</td>
    <td style="text-align: center">x<sub>n</sub></td>
    <td style="text-align: center">x<sub>1</sub></td>
    <td style="text-align: center">...</td>
    <td style="text-align: center">x<sub>n</sub></td>
    <td style="text-align: center">x<sub>1</sub></td>
    <td style="text-align: center">...</td>
    <td style="text-align: center">x<sub>n</sub></td>
    <td style="text-align: center">x<sub>1</sub></td>
    <td style="text-align: center">...</td>
    <td style="text-align: center">x<sub>n</sub></td>
    <td style="text-align: center">x<sub>1</sub></td>
    <td style="text-align: center">...</td>
    <td style="text-align: center">x<sub>n</sub></td>
    <td style="text-align: center">x<sub>1</sub></td>
    <td style="text-align: center">...</td>
    <td style="text-align: center">x<sub>n</sub></td>
  </tr>
</table>

### Image Definitions
<<< @/../model/mrd_image.yml

Notes on `Image` fields:
1. `position`: This is different than DICOM's ImageOrientationPatient, which defines the center of the first (typically top-left) voxel.
2. `colDir`: If the image is [flipped or rotated to bring them into standard DICOM orientation](http://gdcm.sourceforge.net/wiki/index.php/Orientation), ***this field still corresponds to the acquisition readout/frequency direction***, but the `ImageRowDir` should be set in the `meta` attributes.
3. `lineDir`: If the image is [flipped or rotated to bring them into standard DICOM orientation](http://gdcm.sourceforge.net/wiki/index.php/Orientation), ***this field still corresponds to the 2D phase encoding direction***, but the `ImageColumnDir` should be set in the `meta` attributes.
4. `sliceDir`: For 3D data, the slice normal, i.e. cross-product of `readDir` and `phaseDir`. If the image is [flipped or rotated to bring them into standard DICOM orientation](http://gdcm.sourceforge.net/wiki/index.php/Orientation), ***this field still corresponds to the 3D phase encoding direction***, but the `ImageSliceDir` should be set in the `meta` attributes.


## MRD Waveform

### Overview
Physiological data such as electrocardiograms, pulse oximetry, or external triggering sources are stored as individual waveforms along with a fixed Waveform header for metadata.

The `waveformId` field in the `Waveform` record describes the type of physiological data stored.
Waveform ID numbers < 1024 are reserved, while numbers >= 1024 can be used to define custom physiological data.
For custom Waveform IDs, corresponding `WaveformInformation` entries should be added to the [MRD header](#mrd-header) to describe the data interpretation.

Waveform data is streamed as an `uint32` array with dimensions `[channels, samples]`, ordered by looping through samples and then through channels:
<style>
 .smalltable td {
   font-size:       80%;
   border-collapse: collapse;
   border-spacing:  0;
   border-width:    0;
   padding:         3px;
   border:          1px solid lightgray
 }
</style>

<table class="smalltable">
    <tr>
        <td style="text-align: center" colspan="3">Channel 1</td>
        <td style="text-align: center" colspan="3">Channel 2</td>
        <td style="text-align: center" rowspan="2">...</td>
        <td style="text-align: center" colspan="3">Channel n</td>
    </tr>
    <tr>
        <td style="text-align: center">w<sub>1</sub></td>
        <td style="text-align: center">...</td>
        <td style="text-align: center">w<sub>n</sub></td>
        <td style="text-align: center">w<sub>1</sub></td>
        <td style="text-align: center">...</td>
        <td style="text-align: center">w<sub>n</sub></td>
        <td style="text-align: center">w<sub>1</sub></td>
        <td style="text-align: center">...</td>
        <td style="text-align: center">w<sub>n</sub></td>
    </tr>
</table>

### Waveform Definitions
<<< @/../model/mrd_waveform.yml

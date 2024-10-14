# MRD Model

The Magnetic Resonance Data (MRD) format is a vendor neutral standard for describing data from MR acquisitions and reconstructions.

MRD version 2 and above uses [Yardl](https://microsoft.github.io/yardl/) to generate stream-oriented SDKs implementing the standard. MRD streaming formats are described [here](format).

The Model Definitions below are described using the [Yardl language](https://microsoft.github.io/yardl/cpp/language.html), and can be found in the `model/` subdirectory of the MRD repository.
Click to expand the full model file in each component section below.


## MRD Protocol

The MRD Protocol describes an MRD stream or file, which contains:

1.  The [MRD header](#mrd-header) containing general metadata describing the acquisition, including MR system details and k-space sampling.
2.  A sequence of MRD datatypes that may be one of:
    1.  [Raw k-space data](#mrd-acquisition), stored as individual readout acquisitions.
    2.  [Image data](#mrd-image), stored as sets of 2D or 3D arrays.
    3.  [Waveforms](#mrd-waveform), storing physiological data such as electrocardiograms, pulse oximetry, or external triggering sources.
    4.  [Intermediate data](#mrd-intermediate-types), commonly used in MR image reconstruction pipelines.

::: details Click to view MRD Protocol definitions
<<< @/../model/mrd_protocol.yml
:::


## MRD Header

The MRD Header contains general metadata describing the acquisition, including MR system details and k-space sampling.

The header contains a small set of mandatory parameters common to all MR acquisitions, but is extensible to parameters for specialized acquisitions such as b-values, venc, magnetization preparation durations, etc.

The most critical elements for image reconstruction are contained in the `encoding` field of the header, which describes the encoded spaced as well as the target reconstructed space.
This section allows reconstruction software to determine matrix sizes, oversampling factors, partial Fourier, etc.
An experiment can have multiple encoding spaces and it is possible to indicate on each acquired data readout, which encoding space the data belongs to (see the `encodingSpaceRef` field in [MRD Acquisition](#mrd-acquisition)).

::: details Click to view MRD Header definitions
<<< @/../model/mrd_header.yml
:::


## MRD Acquisition

Raw k-space data is stored as individual readout Acquisitions.
Each readout contains the complex raw data for all channels, a fixed header for metadata including encoding loop counters, and optionally corresponding k-space trajectory information.

Acquisition data is stored as a complex float array with dimensions `[coils, samples]`.

k-space trajectory information is optionally included with each readout as a float array with dimensions `[basis, samples]`.

::: details Click to view MRD Acquisition definitions
<<< @/../model/mrd_acquisition.yml
:::


## MRD Image

Image data is stored as either sets of 2D or 3D arrays with a fixed Image header of common properties and metadata.
Images can be organized into series of common types and multi-channel data is supported for non-coil-combined images.

Image data is organized as a 4-D array of the chosen image data type with dimensions `[channel, z, y, x]`.

::: details Click to view MRD Image definitions
<<< @/../model/mrd_image.yml
:::


## MRD Waveform

Physiological data such as electrocardiograms, pulse oximetry, or external triggering sources are stored as individual waveforms along with a fixed Waveform header for metadata.

The `waveformId` field in the `Waveform` record describes the type of physiological data stored.
For custom Waveform IDs, corresponding `WaveformInformation` entries should be added to the [MRD header](#mrd-header) to describe the data interpretation.

Waveform data is streamed as an `uint32` array with dimensions `[channels, samples]`.

::: details Click to view MRD Waveform definitions
<<< @/../model/mrd_waveform.yml
:::


## MRD Intermediate Types

MRD includes definitions for intermediate data types commonly used in MR image reconstruction, including `Acquisitions` "bucketed" by encoding parameters,
buffered k-space data, arrays of `Images`, and dynamic multi-dimensional arrays.

::: details Click to view MRD Intermediate definitions
<<< @/../model/mrd_intermediate.yml
:::

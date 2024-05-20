# Magnetic Resonance Data (MRD) Format
The Magnetic Resonance Data (MRD) format is a vendor neutral standard for describing data from MR acquisitions and reconstructions.

MRD version 2.0.0+ uses [Yardl](https://microsoft.github.io/yardl/) to generate stream-oriented SDKs implementing the standard.
The standard is described in Yardl format (YAML) in the `model/` subdirectory of the MRD repository.
See the [MRD File Format](FileFormat) description for more details.

The MRD Protocol describes an MRD stream or file, which contains:

1.  The [MRD Header](mrd_header.md) containing general metadata describing the acquisition, including MR system details and k-space sampling.
    The header contains a small set of mandatory parameters common to all MR acquisitions, but is extensible to parameters for specialized acquisitions such as b-values, venc, magnetization preparation durations, etc.
    The MRD header is described by a [Yardl model file](../model/mrd_header.yml).

2.  A sequence of MRD datatypes that may be one of:

    1.  [Raw k-space data](mrd_acquisition.md) is stored as individual readout acquisitions.
        Each readout contains the [complex raw data](RawData) for all channels, a fixed [Acquisition Header](AcquisitionHeader) for metadata including [encoding loop counters](EncodingCounters), and optionally corresponding [k-space trajectory](Trajectory) information.
        Most datasets will be comprised of many acquisitions, each stored individually with its own AcquisitionHeader, optional trajectory, and raw data.

    2.  [Image data](mrd_image.md) is stored as either sets of 2D or 3D arrays with a fixed [Image Header](ImageHeader) of common properties and metadata.
        Images can be organized into series of common types and multi-channel data is supported for non-coil-combined images.

    3.  Physiological data such as electrocardiograms, pulse oximetry, or external triggering sources are stored as individual [waveforms](mrd_waveform.md) along with a fixed [WaveformHeader](WaveformHeader) for metadata.

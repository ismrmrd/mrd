# MRD Acquisition
Raw k-space data is stored in MRD format as individual readout Acquisitions, described in [mrd_acquisition.yml](../model/mrd_acquisition.yml).

Each Acquisition contains the complex raw data for all channels, a fixed header, and optionally corresponding k-space trajectory information.
Most datasets will be comprised of many Acquisitions.

(AcquisitionHeader)=
## Acquisition Header
An MRD Acquisition accompanies each readout containing metadata common to most data.
It is of a fixed size and thus fields cannot be added, removed, or otherwise repurposed.
It contains the following information:

| Field                 | Description                                                                                                         | Type
| --                    | --                                                                                                                  | --
| flags                 | A bit mask of common attributes applicable to individual acquisition readouts                                       | uint64
| idx                   | Encoding loop counters, as defined [below](EncodingCounters)                                                        | EncodingCounters
| measurementUid        | Unique ID corresponding to the readout                                                                              | uint32
| scan_counter          | Zero-indexed incrementing counter for readouts                                                                      | uint32?
| acquisitionTimeStamp  | Clock time stamp (e.g. milliseconds since midnight)                                                                 | uint32?
| physiologyTimeStamp   | Time stamps relative to physiological triggering                                                                    | uint32*
| channelOrder          | TODO                                                                                                                | uint32*
| discardPre            | Number of readout samples to be discarded at the beginning (e.g. if the ADC is active during gradient events)       | uint32?
| discardPost           | Number of readout samples to be discarded at the end (e.g. if the ADC is active during gradient events)             | uint32?
| centerSample          | Index of the readout sample corresponing to k-space center (zero indexed)                                           | uint32?
| encodingSpaceRef      | Indexed reference to the encoding spaces enumerated in the MRD (xml) header                                         | uint32?
| sampleTimeUs          | Readout bandwidth, as time between samples in microseconds                                                          | float32?
| position              | Center of the excited volume, in (left, posterior, superior) (LPS) coordinates relative to isocenter in millimeters | float32[3]
| readDir               | Directional cosine of readout/frequency encoding                                                                    | float32[3]
| phaseDir              | Directional cosine of phase encoding (2D)                                                                           | float32[3]
| sliceDir              | Directional cosine of slice normal, i.e. cross-product of read_dir and phase_dir                                    | float32[3]
| patientTablePosition  | Offset position of the patient table, in LPS coordinates                                                            | float32[3]
| userInt               | User-defined integer parameters, multiplicity defined by ISMRMRD_USER_INTS (currently 8)                            | int32*
| userFloat             | User-defined float parameters, multiplicity defined by ISMRMRD_USER_FLOATS (currently 8)                            | float32*
| data                  | Raw AcquisitionData as defined [below](RawData)                                                                     | AcqusititionData
| trajectory            | Trajectory data as defined [below](Trajectory)                                                                      | TrajectoryData

<!-- A reference implementation for serialization/deserialization of the AcquisitionHeader can be found in [serialization.cpp](../libsrc/serialization.cpp). -->

(EncodingCounters)=
### EncodingCounters
MR acquisitions often loop through a set of counters (e.g. phase encodes) in a complete experiment.
The following encoding counters are referred to by the `idx` field in the Acquisition record.

| Field             | Description                                                            | Type
| --                | --                                                                     | --
| kspaceEncodeStep1 | Phase encoding line                                                    | uint16?
| kspaceEncodeStep2 | Partition encoding                                                     | uint16?
| average           | Signal average                                                         | uint16?
| slice             | Slice number (multi-slice 2D)                                          | uint16?
| contrast          | Echo number in multi-echo                                              | uint16?
| phase             | Cardiac phase                                                          | uint16?
| repetition        | Counter in repeated/dynamic acquisitions                               | uint16?
| set               | Sets of different preparation, e.g. flow encoding, diffusion weighting | uint16?
| segment           | Counter for segmented acquisitions                                     | uint16?
| user              | User defined counters                                                  | uint16*

<!-- A reference implementation for serialization/deserialization of the EncodingCounters can be found in [serialization.cpp](../libsrc/serialization.cpp). -->

### AcquisitionFlags
The `flags` field in the Acquisition record is a 64 bit mask that can be used to indicate specific attributes of the corresponding readout.
One usage of these flags is to trigger the processing of data when a condition is met, e.g. the last readout for the current slice.
Avaiable flags are defined in the `AcquisitionFlags` enum of [mrd_acquisition.yml](../model/mrd_acquisition.yml).

(Trajectory)=
## Trajectory (k-space)

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

k-space trajectory information is optionally included with each readout as a `float32` array with dimensions `[basis, samples]`.

<!-- ... with dimensionality specified by the ``trajectory_dimensions`` field in the AcquisitionHeader.  Common values are ``2`` for 2D radial (k<sub>x</sub>, k<sub>y</sub>), ``3`` for 3D radial (k<sub>x</sub>, k<sub>y</sub>, k<sub>z</sub>).  Trajectory information is omitted if ``trajectory_dimensions`` is set to ``0``. -->

Trajectory data is organized by looping through the dimensions first then the samples:
  - For 2D trajectory data:
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

  - For 3D trajectory data:

    TODO

    <!-- <table class="smalltable">
      <tr>
        <td style="text-align: center" colspan="3">Sample 1</td>
        <td style="text-align: center" colspan="3">Sample 2</td>
        <td style="text-align: center" rowspan="2">...</td>
        <td style="text-align: center" colspan="3">Sample n</td>
      </tr>
      <tr>
        <td style="text-align: center">k<sub>x</sub></td>
        <td style="text-align: center">k<sub>y</sub></td>
        <td style="text-align: center">k<sub>z</sub></td>
        <td style="text-align: center">k<sub>x</sub></td>
        <td style="text-align: center">k<sub>y</sub></td>
        <td style="text-align: center">k<sub>z</sub></td>
        <td style="text-align: center">k<sub>x</sub></td>
        <td style="text-align: center">k<sub>y</sub></td>
        <td style="text-align: center">k<sub>z</sub></td>
      </tr>
    </table> -->


(RawData)=
## Raw Data
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

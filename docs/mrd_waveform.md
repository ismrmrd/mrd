# MRD Waveform
Physiological monitoring data such as electrocardiograms, pulse oximetry, or external triggering may accompany MR acquisitions.
These physiological data are stored in MRD as a combination of a fixed [WaveformHeader](WaveformHeader) and the [raw physiological waveforms](WaveformSamples).

(WaveformHeader)=
## Waveform Header
The Waveform record contains metadata associated with a set of waveform data and has the following fields:
| Field           | Description                                           | Type
| --              | --                                                    | --
| flags           | Bit field with flags                                  | uint64
| measurementUid  | Unique ID for this measurement                        | uint32
| scanCounter     | Number of the acquisition after this waveform         | uint32
| timeStamp       | Starting timestamp of this waveform                   | uint32
| sampleTimeUs    | Time between samples in microseconds                  | float
| waveformId      | ID matching types defined [below](WaveformIDs)        | uint32
| data            | Waveform Samples as defined [below](WaveformSamples)  | WaveformSamples

<!-- A reference implementation for serialization/deserialization of the WaveformHeader can be found in [serialization.cpp](../libsrc/serialization.cpp). -->

(WaveformIDs)=
### Waveform IDs
The `waveform_id` field in the Waveform record describes the type of physiological data stored.
The following ID numbers are defined in the `WaveformType` enum in [mrd_header.yml](../model/mrd_waveform.yml):

| Value | Name                |
| --    | --                  |
|  0    | ECG                 |
|  1    | Pulse Oximetry      |
|  2    | Respiratory         |
|  3    | External Waveform 1 |
|  4    | External Waveform 2 |

For each type of `waveform_id` included in the dataset, a corresponding `WaveformInformation` entry is found in the MRD header to describe the data interpretation.

<!-- Physiological data used for triggering may have an associated "trigger" channel as detected by the MR system.  The ``waveformTriggerChannel`` indicates the channel index (0-indexed) which contains the detected triggers and is omitted if no trigger data is present. -->

Waveform ID numbers less than 1024 are reserved while numbers greater than or equal to 1024 can be used to define custom physiological data.
For custom waveform_ids, corresponding `WaveformInformation` entries should be added to the MRD header to describe the data interpretation.


(WaveformSamples)=
## Waveform Data

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

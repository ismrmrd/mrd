# MRD Header
<!-- The flexible data structure is defined by the xml schema definition in [schema/ismrmrd.xsd](../schema/ismrmrd.xsd). An example of an XML file for a Cartesian 3D acquisition can be found [schema/ismrmrd_example.xml](../schema/ismrmrd_example.xml). -->

The MRD Header is defined as a Yardl record in [model/mrd_header.yml](../model/mrd_header.yml).

| Field                         | Description
| --                            | --
| version                       | MRD Version number
| subjectInformation            | Patient metadata
| measurementInformation        | Protocol, series, datetime metadata
| acquisitionSystemInformation  | Instrument system information
| experimentalConditions        | H1 Resonance Frequency
| encoding                      | Described encoded space, target reconstructed space, trajectory
| sequenceParameters            | Sequence-specific parameters
| userParameters                | Custom user parameters
| waveformInformation           | Waveform name, type, and user parameters

The most critical elements for image reconstruction are contained in the `encoding` field of the header, which describes the encoded spaced and also the target reconstructed space.
This section allows the reconstruction program to determine matrix sizes, oversampling factors, partial Fourier, etc.
An experiment can have multiple encoding spaces and it is possible to indicate on each acquired data readout, which encoding space the data belongs to (see the `encodingSpaceRef` field of [MRD Acquisition](AcquisitionHeader)).

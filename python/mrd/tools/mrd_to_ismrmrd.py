#!/usr/bin/env python3
"""Convert MRD stream to ISMRMRD stream."""

import sys
import argparse
import itertools
from typing import BinaryIO
import datetime

import ismrmrd
import ismrmrd.serialization
import mrd
import numpy as np

from xsdata.models.datatype import XmlDate, XmlTime


def yardl_time_to_time(yardl_time) -> datetime.time:
    """Convert yardl.Time to datetime.time."""
    # yardl.Time stores time as nanoseconds since midnight
    total_ns = yardl_time.nanoseconds_since_midnight

    # Convert to time components
    total_seconds = total_ns // 1_000_000_000
    remaining_ns = total_ns % 1_000_000_000

    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    microseconds = remaining_ns // 1000

    return datetime.time(hour=hours, minute=minutes, second=seconds, microsecond=microseconds)


def convert_header(mrd_header: mrd.Header) -> ismrmrd.xsd.ismrmrdHeader:
    """Convert MRD header to ISMRMRD header."""
    header = ismrmrd.xsd.ismrmrdHeader()

    # Version
    if mrd_header.version:
        header.version = mrd_header.version

    # Subject information
    if mrd_header.subject_information:
        subj = ismrmrd.xsd.subjectInformationType()
        subj_info = mrd_header.subject_information

        if subj_info.patient_name:
            subj.patientName = subj_info.patient_name
        if subj_info.patient_weight_kg is not None:
            subj.patientWeight_kg = subj_info.patient_weight_kg
        if subj_info.patient_height_m is not None:
            subj.patientHeight_m = subj_info.patient_height_m
        if subj_info.patient_id:
            subj.patientID = subj_info.patient_id
        if subj_info.patient_birthdate:
            subj.patientBirthdate = XmlDate.from_date(subj_info.patient_birthdate)
        if subj_info.patient_gender:
            gender_map = {mrd.PatientGender.F: 'F', mrd.PatientGender.M: 'M', mrd.PatientGender.O: 'O'}
            if subj_info.patient_gender in gender_map:
                subj.patientGender = gender_map[subj_info.patient_gender]

        header.subjectInformation = subj

    # Study information
    if mrd_header.study_information:
        study = ismrmrd.xsd.studyInformationType()
        study_info = mrd_header.study_information

        if study_info.study_date:
            study.studyDate = XmlDate.from_date(study_info.study_date)
        if study_info.study_time:
            study.studyTime = XmlTime.from_time(yardl_time_to_time(study_info.study_time))
        if study_info.study_id:
            study.studyID = study_info.study_id
        if study_info.accession_number:
            study.accessionNumber = study_info.accession_number
        if study_info.referring_physician_name:
            study.referringPhysicianName = study_info.referring_physician_name
        if study_info.study_description:
            study.studyDescription = study_info.study_description
        if study_info.study_instance_uid:
            study.studyInstanceUID = study_info.study_instance_uid
        if study_info.body_part_examined:
            study.bodyPartExamined = study_info.body_part_examined

        header.studyInformation = study

    # Measurement information
    if mrd_header.measurement_information:
        meas = ismrmrd.xsd.measurementInformationType()
        meas_info = mrd_header.measurement_information

        if meas_info.measurement_id:
            meas.measurementID = meas_info.measurement_id
        if meas_info.series_date:
            meas.seriesDate = XmlDate.from_date(meas_info.series_date)
        if meas_info.series_time:
            meas.seriesTime = XmlTime.from_time(yardl_time_to_time(meas_info.series_time))

        # Patient position
        pos_map = {
            mrd.PatientPosition.H_FS: ismrmrd.xsd.patientPositionType.HFS,
            mrd.PatientPosition.H_FP: ismrmrd.xsd.patientPositionType.HFP,
            mrd.PatientPosition.H_FDR: ismrmrd.xsd.patientPositionType.HFDR,
            mrd.PatientPosition.H_FDL: ismrmrd.xsd.patientPositionType.HFDL,
            mrd.PatientPosition.F_FDR: ismrmrd.xsd.patientPositionType.FFDR,
            mrd.PatientPosition.F_FDL: ismrmrd.xsd.patientPositionType.FFDL,
            mrd.PatientPosition.F_FP: ismrmrd.xsd.patientPositionType.FFP,
            mrd.PatientPosition.F_FS: ismrmrd.xsd.patientPositionType.FFS
        }
        if meas_info.patient_position in pos_map:
            meas.patientPosition = pos_map[meas_info.patient_position]

        if meas_info.initial_series_number is not None:
            meas.initialSeriesNumber = meas_info.initial_series_number
        if meas_info.protocol_name:
            meas.protocolName = meas_info.protocol_name
        if meas_info.series_description:
            meas.seriesDescription = meas_info.series_description
        if meas_info.series_instance_uid_root:
            meas.seriesInstanceUIDRoot = meas_info.series_instance_uid_root
        if meas_info.frame_of_reference_uid:
            meas.frameOfReferenceUID = meas_info.frame_of_reference_uid

        if meas_info.referenced_image_sequence:
            ref_seq = ismrmrd.xsd.referencedImageSequenceType()
            for uid in meas_info.referenced_image_sequence.referenced_sop_instance_uid:
                ref_seq.referencedSOPInstanceUID.append(uid)
            meas.referencedImageSequence = ref_seq

        header.measurementInformation = meas

    # Acquisition system information
    if mrd_header.acquisition_system_information:
        sys_info = ismrmrd.xsd.acquisitionSystemInformationType()
        acq_sys = mrd_header.acquisition_system_information

        if acq_sys.system_vendor:
            sys_info.systemVendor = acq_sys.system_vendor
        if acq_sys.system_model:
            sys_info.systemModel = acq_sys.system_model
        if acq_sys.system_field_strength_t is not None:
            sys_info.systemFieldStrength_T = acq_sys.system_field_strength_t
        if acq_sys.relative_receiver_noise_bandwidth is not None:
            sys_info.relativeReceiverNoiseBandwidth = acq_sys.relative_receiver_noise_bandwidth
        if acq_sys.receiver_channels is not None:
            sys_info.receiverChannels = acq_sys.receiver_channels

        if acq_sys.coil_label:
            for label in acq_sys.coil_label:
                coil = ismrmrd.xsd.coilLabelType()
                if label.coil_number is not None:
                    coil.coilNumber = label.coil_number
                if label.coil_name:
                    coil.coilName = label.coil_name
                sys_info.coilLabel.append(coil)

        if acq_sys.institution_name:
            sys_info.institutionName = acq_sys.institution_name
        if acq_sys.station_name:
            sys_info.stationName = acq_sys.station_name
        if acq_sys.device_id:
            sys_info.deviceID = acq_sys.device_id
        if acq_sys.device_serial_number:
            sys_info.deviceSerialNumber = acq_sys.device_serial_number

        header.acquisitionSystemInformation = sys_info

    # Experimental conditions
    exp = ismrmrd.xsd.experimentalConditionsType()
    exp.H1resonanceFrequency_Hz = mrd_header.experimental_conditions.h1resonance_frequency_hz
    header.experimentalConditions = exp

    # Encoding
    if not mrd_header.encoding:
        raise ValueError("No encoding found in MRD header")

    for enc_mrd in mrd_header.encoding:
        enc = ismrmrd.xsd.encodingType()

        # Encoded space
        enc_space = ismrmrd.xsd.encodingSpaceType()
        enc_space.matrixSize = ismrmrd.xsd.matrixSizeType(
            x=enc_mrd.encoded_space.matrix_size.x,
            y=enc_mrd.encoded_space.matrix_size.y,
            z=enc_mrd.encoded_space.matrix_size.z
        )
        enc_space.fieldOfView_mm = ismrmrd.xsd.fieldOfViewMm(
            x=enc_mrd.encoded_space.field_of_view_mm.x,
            y=enc_mrd.encoded_space.field_of_view_mm.y,
            z=enc_mrd.encoded_space.field_of_view_mm.z
        )
        enc.encodedSpace = enc_space

        # Recon space
        recon_space = ismrmrd.xsd.encodingSpaceType()
        recon_space.matrixSize = ismrmrd.xsd.matrixSizeType(
            x=enc_mrd.recon_space.matrix_size.x,
            y=enc_mrd.recon_space.matrix_size.y,
            z=enc_mrd.recon_space.matrix_size.z
        )
        recon_space.fieldOfView_mm = ismrmrd.xsd.fieldOfViewMm(
            x=enc_mrd.recon_space.field_of_view_mm.x,
            y=enc_mrd.recon_space.field_of_view_mm.y,
            z=enc_mrd.recon_space.field_of_view_mm.z
        )
        enc.reconSpace = recon_space

        # Encoding limits
        if enc_mrd.encoding_limits:
            limits = ismrmrd.xsd.encodingLimitsType()

            if enc_mrd.encoding_limits.kspace_encoding_step_0:
                lim = enc_mrd.encoding_limits.kspace_encoding_step_0
                limits.kspace_encoding_step_0 = ismrmrd.xsd.limitType(
                    minimum=lim.minimum, maximum=lim.maximum, center=lim.center
                )
            if enc_mrd.encoding_limits.kspace_encoding_step_1:
                lim = enc_mrd.encoding_limits.kspace_encoding_step_1
                limits.kspace_encoding_step_1 = ismrmrd.xsd.limitType(
                    minimum=lim.minimum, maximum=lim.maximum, center=lim.center
                )
            if enc_mrd.encoding_limits.kspace_encoding_step_2:
                lim = enc_mrd.encoding_limits.kspace_encoding_step_2
                limits.kspace_encoding_step_2 = ismrmrd.xsd.limitType(
                    minimum=lim.minimum, maximum=lim.maximum, center=lim.center
                )
            if enc_mrd.encoding_limits.average:
                lim = enc_mrd.encoding_limits.average
                limits.average = ismrmrd.xsd.limitType(
                    minimum=lim.minimum, maximum=lim.maximum, center=lim.center
                )
            if enc_mrd.encoding_limits.slice:
                lim = enc_mrd.encoding_limits.slice
                limits.slice = ismrmrd.xsd.limitType(
                    minimum=lim.minimum, maximum=lim.maximum, center=lim.center
                )
            if enc_mrd.encoding_limits.contrast:
                lim = enc_mrd.encoding_limits.contrast
                limits.contrast = ismrmrd.xsd.limitType(
                    minimum=lim.minimum, maximum=lim.maximum, center=lim.center
                )
            if enc_mrd.encoding_limits.phase:
                lim = enc_mrd.encoding_limits.phase
                limits.phase = ismrmrd.xsd.limitType(
                    minimum=lim.minimum, maximum=lim.maximum, center=lim.center
                )
            if enc_mrd.encoding_limits.repetition:
                lim = enc_mrd.encoding_limits.repetition
                limits.repetition = ismrmrd.xsd.limitType(
                    minimum=lim.minimum, maximum=lim.maximum, center=lim.center
                )
            if enc_mrd.encoding_limits.set:
                lim = enc_mrd.encoding_limits.set
                limits.set = ismrmrd.xsd.limitType(
                    minimum=lim.minimum, maximum=lim.maximum, center=lim.center
                )
            if enc_mrd.encoding_limits.segment:
                lim = enc_mrd.encoding_limits.segment
                limits.segment = ismrmrd.xsd.limitType(
                    minimum=lim.minimum, maximum=lim.maximum, center=lim.center
                )

            enc.encodingLimits = limits

        # Trajectory
        if enc_mrd.trajectory:
            traj_map = {
                mrd.Trajectory.CARTESIAN: ismrmrd.xsd.trajectoryType.CARTESIAN,
                mrd.Trajectory.EPI: ismrmrd.xsd.trajectoryType.EPI,
                mrd.Trajectory.RADIAL: ismrmrd.xsd.trajectoryType.RADIAL,
                mrd.Trajectory.GOLDENANGLE: ismrmrd.xsd.trajectoryType.GOLDENANGLE,
                mrd.Trajectory.SPIRAL: ismrmrd.xsd.trajectoryType.SPIRAL,
                mrd.Trajectory.OTHER: ismrmrd.xsd.trajectoryType.OTHER
            }
            if enc_mrd.trajectory in traj_map:
                enc.trajectory = traj_map[enc_mrd.trajectory]

        # Trajectory description (if present)
        if enc_mrd.trajectory_description:
            traj_desc = ismrmrd.xsd.trajectoryDescriptionType()
            if enc_mrd.trajectory_description.identifier:
                traj_desc.identifier = enc_mrd.trajectory_description.identifier
            enc.trajectoryDescription = traj_desc

        # Parallel imaging
        if enc_mrd.parallel_imaging:
            parallel = ismrmrd.xsd.parallelImagingType()
            par_img = enc_mrd.parallel_imaging

            if par_img.acceleration_factor:
                acc = ismrmrd.xsd.accelerationFactorType()
                if par_img.acceleration_factor.kspace_encoding_step_1 is not None:
                    acc.kspace_encoding_step_1 = par_img.acceleration_factor.kspace_encoding_step_1
                if par_img.acceleration_factor.kspace_encoding_step_2 is not None:
                    acc.kspace_encoding_step_2 = par_img.acceleration_factor.kspace_encoding_step_2
                parallel.accelerationFactor = acc

            if par_img.calibration_mode:
                calib_map = {
                    mrd.CalibrationMode.EMBEDDED: ismrmrd.xsd.calibrationModeType.EMBEDDED,
                    mrd.CalibrationMode.INTERLEAVED: ismrmrd.xsd.calibrationModeType.INTERLEAVED,
                    mrd.CalibrationMode.SEPARATE: ismrmrd.xsd.calibrationModeType.SEPARATE,
                    mrd.CalibrationMode.EXTERNAL: ismrmrd.xsd.calibrationModeType.EXTERNAL,
                    mrd.CalibrationMode.OTHER: ismrmrd.xsd.calibrationModeType.OTHER
                }
                if par_img.calibration_mode in calib_map:
                    parallel.calibrationMode = calib_map[par_img.calibration_mode]

            if par_img.interleaving_dimension:
                interleave_map = {
                    mrd.InterleavingDimension.PHASE: ismrmrd.xsd.interleavingDimensionType.PHASE,
                    mrd.InterleavingDimension.REPETITION: ismrmrd.xsd.interleavingDimensionType.REPETITION,
                    mrd.InterleavingDimension.CONTRAST: ismrmrd.xsd.interleavingDimensionType.CONTRAST,
                    mrd.InterleavingDimension.AVERAGE: ismrmrd.xsd.interleavingDimensionType.AVERAGE,
                    mrd.InterleavingDimension.OTHER: ismrmrd.xsd.interleavingDimensionType.OTHER
                }
                if par_img.interleaving_dimension in interleave_map:
                    parallel.interleavingDimension = interleave_map[par_img.interleaving_dimension]

            enc.parallelImaging = parallel

        # Echo train length
        if enc_mrd.echo_train_length is not None:
            enc.echoTrainLength = enc_mrd.echo_train_length

        header.encoding.append(enc)

    # Sequence parameters
    if mrd_header.sequence_parameters:
        seq = ismrmrd.xsd.sequenceParametersType()
        seq_params = mrd_header.sequence_parameters

        for tr in seq_params.t_r:
            seq.TR.append(tr)
        for te in seq_params.t_e:
            seq.TE.append(te)
        for ti in seq_params.t_i:
            seq.TI.append(ti)
        for fa in seq_params.flip_angle_deg:
            seq.flipAngle_deg.append(fa)
        if seq_params.sequence_type:
            seq.sequence_type = seq_params.sequence_type
        for es in seq_params.echo_spacing:
            seq.echo_spacing.append(es)

        header.sequenceParameters = seq

    # User parameters
    if mrd_header.user_parameters:
        user_params = ismrmrd.xsd.userParametersType()

        for param in mrd_header.user_parameters.user_parameter_long:
            up = ismrmrd.xsd.userParameterLongType()
            up.name = param.name
            up.value = param.value
            user_params.userParameterLong.append(up)

        for param in mrd_header.user_parameters.user_parameter_double:
            up = ismrmrd.xsd.userParameterDoubleType()
            up.name = param.name
            up.value = param.value
            user_params.userParameterDouble.append(up)

        for param in mrd_header.user_parameters.user_parameter_string:
            up = ismrmrd.xsd.userParameterStringType()
            up.name = param.name
            up.value = param.value
            user_params.userParameterString.append(up)

        for param in mrd_header.user_parameters.user_parameter_base64:
            up = ismrmrd.xsd.userParameterBase64Type()
            up.name = param.name
            up.value = bytes(param.value, 'utf-8')
            user_params.userParameterBase64.append(up)

        header.userParameters = user_params

    return header


def convert_acquisition(mrd_acq: mrd.Acquisition) -> ismrmrd.Acquisition:
    """Convert MRD acquisition to ISMRMRD acquisition."""
    mrd_head = mrd_acq.head

    # Get dimensions
    num_samples = mrd_acq.data.shape[1]
    num_channels = mrd_acq.data.shape[0]
    traj_dims = mrd_acq.trajectory.shape[0] if mrd_acq.trajectory is not None else 0

    # Build the header first
    head = ismrmrd.AcquisitionHeader()
    head.version = 1  # ISMRMRD_VERSION_MAJOR
    head.flags = mrd_head.flags
    head.measurement_uid = mrd_head.measurement_uid
    head.scan_counter = mrd_head.scan_counter or 0
    head.acquisition_time_stamp = int(mrd_head.acquisition_time_stamp_ns or 0 // 1e6)  # ns to ms

    for i in range(ismrmrd.PHYS_STAMPS):
        if i < len(mrd_head.physiology_time_stamp_ns):
            head.physiology_time_stamp[i] = int(mrd_head.physiology_time_stamp_ns[i] // 1e6)  # ns to ms
        else:
            head.physiology_time_stamp[i] = 0

    head.number_of_samples = num_samples
    head.available_channels = num_channels
    head.active_channels = num_channels
    head.discard_pre = mrd_head.discard_pre or 0
    head.discard_post = mrd_head.discard_post or 0
    head.center_sample = mrd_head.center_sample or 0
    head.encoding_space_ref = mrd_head.encoding_space_ref or 0
    head.trajectory_dimensions = traj_dims
    head.sample_time_us = float(mrd_head.sample_time_ns or 0) / 1000.0  # ns to µs

    # Positions and directions
    head.position[:] = mrd_head.position
    head.read_dir[:] = mrd_head.read_dir
    head.phase_dir[:] = mrd_head.phase_dir
    head.slice_dir[:] = mrd_head.slice_dir
    head.patient_table_position[:] = mrd_head.patient_table_position

    # Encoding counters
    head.idx.kspace_encode_step_1 = mrd_head.idx.kspace_encode_step_1 or 0
    head.idx.kspace_encode_step_2 = mrd_head.idx.kspace_encode_step_2 or 0
    head.idx.average = mrd_head.idx.average or 0
    head.idx.slice = mrd_head.idx.slice or 0
    head.idx.contrast = mrd_head.idx.contrast or 0
    head.idx.phase = mrd_head.idx.phase or 0
    head.idx.repetition = mrd_head.idx.repetition or 0
    head.idx.set = mrd_head.idx.set or 0
    head.idx.segment = mrd_head.idx.segment or 0

    # User parameters - initialize all to defaults, then set values
    for i in range(ismrmrd.USER_INTS):
        head.user_int[i] = 0
    for i in range(ismrmrd.USER_FLOATS):
        head.user_float[i] = 0.0
    for i in range(min(len(mrd_head.user_int), ismrmrd.USER_INTS)):
        head.user_int[i] = mrd_head.user_int[i]
    for i in range(min(len(mrd_head.user_float), ismrmrd.USER_FLOATS)):
        head.user_float[i] = mrd_head.user_float[i]

    # Create ISMRMRD acquisition and resize it
    acq = ismrmrd.Acquisition()
    acq.setHead(head)
    acq.data[:] = mrd_acq.data

    # Copy trajectory - both MRD and ISMRMRD use (traj_dims, samples)
    if mrd_acq.trajectory is not None and mrd_acq.trajectory.size > 0:
        acq.traj[:] = mrd_acq.trajectory

    return acq


def convert_waveform(mrd_wfm: mrd.WaveformUint32) -> ismrmrd.Waveform:
    """Convert MRD waveform to ISMRMRD waveform."""
    # Get dimensions from data
    num_channels = mrd_wfm.data.shape[0]
    num_samples = mrd_wfm.data.shape[1]

    # Build the header first
    head = ismrmrd.WaveformHeader()
    head.flags = mrd_wfm.flags
    head.measurement_uid = mrd_wfm.measurement_uid
    head.scan_counter = mrd_wfm.scan_counter
    head.time_stamp = int(mrd_wfm.time_stamp_ns // 1e6)  # ns to ms
    head.sample_time_us = mrd_wfm.sample_time_ns / 1000.0  # ns to µs
    head.waveform_id = mrd_wfm.waveform_id
    head.channels = num_channels
    head.number_of_samples = num_samples

    wfm = ismrmrd.Waveform()
    wfm.setHead(head)
    wfm.data[:] = mrd_wfm.data
    return wfm


def convert_image(mrd_img) -> ismrmrd.Image:
    """Convert MRD image to ISMRMRD image."""
    mrd_head = mrd_img.head
    data = mrd_img.data

    # Get dimensions: data is (channels, z, y, x)
    channels = data.shape[0]
    z = data.shape[1]
    y = data.shape[2]
    x = data.shape[3]

    # Build the ImageHeader first
    head = ismrmrd.ImageHeader()
    head.version = 1 # ISMRMRD_VERSION_MAJOR
    head.flags = mrd_head.flags
    head.measurement_uid = mrd_head.measurement_uid
    head.matrix_size[:] = [x, y, z]
    head.field_of_view[:] = mrd_head.field_of_view
    head.channels = channels
    head.position[:] = mrd_head.position
    head.read_dir[:] = mrd_head.col_dir
    head.phase_dir[:] = mrd_head.line_dir
    head.slice_dir[:] = mrd_head.slice_dir
    head.patient_table_position[:] = mrd_head.patient_table_position
    head.average = mrd_head.average or 0
    head.slice = mrd_head.slice or 0
    head.contrast = mrd_head.contrast or 0
    head.phase = mrd_head.phase or 0
    head.repetition = mrd_head.repetition or 0
    head.set = mrd_head.set or 0
    head.acquisition_time_stamp = int((mrd_head.acquisition_time_stamp_ns or 0) // 1e6)  # ns to ms

    for i in range(ismrmrd.PHYS_STAMPS):
        if i < len(mrd_head.physiology_time_stamp_ns):
            head.physiology_time_stamp[i] = int(mrd_head.physiology_time_stamp_ns[i] // 1e6)  # ns to ms
        else:
            head.physiology_time_stamp[i] = 0

    # Image type and indices
    head.image_type = mrd_head.image_type.value
    head.image_index = mrd_head.image_index or 0
    head.image_series_index = mrd_head.image_series_index or 0

    # Determine data type from dtype
    dtype = data.dtype
    if dtype == np.uint16:
        head.data_type = ismrmrd.DATATYPE_USHORT
    elif dtype == np.int16:
        head.data_type = ismrmrd.DATATYPE_SHORT
    elif dtype == np.uint32:
        head.data_type = ismrmrd.DATATYPE_UINT
    elif dtype == np.int32:
        head.data_type = ismrmrd.DATATYPE_INT
    elif dtype == np.float32:
        head.data_type = ismrmrd.DATATYPE_FLOAT
    elif dtype == np.float64:
        head.data_type = ismrmrd.DATATYPE_DOUBLE
    elif dtype == np.complex64:
        head.data_type = ismrmrd.DATATYPE_CXFLOAT
    elif dtype == np.complex128:
        head.data_type = ismrmrd.DATATYPE_CXDOUBLE
    else:
        raise ValueError(f"Unsupported image data type: {dtype}")

    # User parameters - initialize all to defaults, then set values
    for i in range(ismrmrd.USER_INTS):
        head.user_int[i] = 0
    for i in range(ismrmrd.USER_FLOATS):
        head.user_float[i] = 0.0
    for i in range(min(len(mrd_head.user_int), ismrmrd.USER_INTS)):
        head.user_int[i] = mrd_head.user_int[i]
    for i in range(min(len(mrd_head.user_float), ismrmrd.USER_FLOATS)):
        head.user_float[i] = mrd_head.user_float[i]

    # Convert meta dict to ISMRMRD attribute_string (XML)
    attribute_string = ""
    if mrd_img.meta:
        try:
            # Convert MRD ImageMeta to ISMRMRD Meta format
            # MRD: dict[str, list[ImageMetaValue]]
            # ISMRMRD: dict with single values or lists
            ismrmrd_meta_dict = {}

            for key, value_list in mrd_img.meta.items():
                # Extract the actual values from ImageMetaValue objects
                extracted_values = []
                for meta_value in value_list:
                    extracted_values.append(meta_value.value)

                # If single value, unwrap the list
                if len(extracted_values) == 1:
                    ismrmrd_meta_dict[key] = extracted_values[0]
                else:
                    ismrmrd_meta_dict[key] = extracted_values

            # Create ISMRMRD Meta and serialize to XML
            ismrmrd_meta = ismrmrd.Meta(ismrmrd_meta_dict)
            attribute_string = ismrmrd_meta.serialize()
        except Exception:
            # If serialization fails, use empty string
            pass

    head.attribute_string_len = len(attribute_string)

    # Create ISMRMRD image, resize it, and set header
    img = ismrmrd.Image()
    # Note: resize signature is (nc, nz, ny, nx) - same order as MRD!
    img.resize(channels, z, y, x)
    img.setHead(head)
    img.data[:] = data

    # Set attribute_string if present
    if attribute_string:
        img.attribute_string = attribute_string

    return img


def stream_mrd_to_ismrmrd(reader: mrd.BinaryMrdReader, serializer: ismrmrd.serialization.ProtocolSerializer) -> None:
    """Stream MRD data to ISMRMRD serializer."""
    # Read and convert header
    mrd_header = reader.read_header()
    if mrd_header:
        ismrmrd_header = convert_header(mrd_header)
        serializer.serialize(ismrmrd_header)

    # Read and convert data items
    for mrd_item in reader.read_data():
        if isinstance(mrd_item, mrd.StreamItem.Acquisition):
            ismrmrd_item = convert_acquisition(mrd_item.value)
        elif isinstance(mrd_item, mrd.StreamItem.WaveformUint32):
            ismrmrd_item = convert_waveform(mrd_item.value)
        elif isinstance(mrd_item, mrd.StreamItem.ImageUint16):
            ismrmrd_item = convert_image(mrd_item.value)
        elif isinstance(mrd_item, mrd.StreamItem.ImageInt16):
            ismrmrd_item = convert_image(mrd_item.value)
        elif isinstance(mrd_item, mrd.StreamItem.ImageUint32):
            ismrmrd_item = convert_image(mrd_item.value)
        elif isinstance(mrd_item, mrd.StreamItem.ImageInt32):
            ismrmrd_item = convert_image(mrd_item.value)
        elif isinstance(mrd_item, mrd.StreamItem.ImageFloat):
            ismrmrd_item = convert_image(mrd_item.value)
        elif isinstance(mrd_item, mrd.StreamItem.ImageDouble):
            ismrmrd_item = convert_image(mrd_item.value)
        elif isinstance(mrd_item, mrd.StreamItem.ImageComplexFloat):
            ismrmrd_item = convert_image(mrd_item.value)
        elif isinstance(mrd_item, mrd.StreamItem.ImageComplexDouble):
            ismrmrd_item = convert_image(mrd_item.value)
        else:
            raise ValueError("Unsupported MRD StreamItem type")
        if ismrmrd_item is None:
            raise ValueError("Conversion resulted in invalid ISMRMRD item")
        serializer.serialize(ismrmrd_item)


def convert_mrd_to_ismrmrd(input_stream: BinaryIO, output_stream: BinaryIO) -> None:
    """
    Convert MRD stream to ISMRMRD stream.

    Args:
        input_stream: Binary input stream containing MRD data
        output_stream: Binary output stream for ISMRMRD data
    """
    # Create MRD reader and ISMRMRD serializer
    with mrd.BinaryMrdReader(input_stream) as reader:
        with ismrmrd.serialization.ProtocolSerializer(output_stream) as serializer:
            stream_mrd_to_ismrmrd(reader, serializer)


def main():
    parser = argparse.ArgumentParser(
        description="Convert MRD stream to ISMRMRD stream"
    )
    parser.add_argument(
        '-i', '--input',
        type=str,
        help="Input MRD stream (default: stdin)"
    )
    parser.add_argument(
        '-o', '--output',
        type=str,
        help="Output ISMRMRD stream (default: stdout)"
    )

    args = parser.parse_args()

    # Open input stream
    if args.input:
        try:
            input_stream = open(args.input, 'rb')
        except IOError as e:
            print(f"Failed to open input file for reading: {e}", file=sys.stderr)
            return 1
    else:
        input_stream = sys.stdin.buffer

    # Open output stream
    if args.output:
        try:
            output_stream = open(args.output, 'wb')
        except IOError as e:
            print(f"Failed to open output file for writing: {e}", file=sys.stderr)
            return 1
    else:
        output_stream = sys.stdout.buffer

    try:
        convert_mrd_to_ismrmrd(input_stream, output_stream)
        return 0
    finally:
        if args.input:
            input_stream.close()
        if args.output:
            output_stream.close()


if __name__ == "__main__":
    sys.exit(main())

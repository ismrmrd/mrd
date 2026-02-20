#!/usr/bin/env python3
"""Convert ISMRMRD stream to MRD stream."""

import sys
import argparse
import itertools
from typing import BinaryIO

import ismrmrd
import ismrmrd.serialization
import mrd
import numpy as np


def convert_header(ismrmrd_header: ismrmrd.xsd.ismrmrdHeader) -> mrd.Header:
    """Convert ISMRMRD header to MRD header."""
    header = mrd.Header()

    # Version
    if ismrmrd_header.version:
        header.version = ismrmrd_header.version

    # Subject information
    if ismrmrd_header.subjectInformation:
        subject = mrd.SubjectInformationType()
        subj_info = ismrmrd_header.subjectInformation

        if subj_info.patientName:
            subject.patient_name = subj_info.patientName
        if subj_info.patientWeight_kg:
            subject.patient_weight_kg = subj_info.patientWeight_kg
        if subj_info.patientHeight_m:
            subject.patient_height_m = subj_info.patientHeight_m
        if subj_info.patientID:
            subject.patient_id = subj_info.patientID
        if subj_info.patientBirthdate:
            subject.patient_birthdate = subj_info.patientBirthdate.to_date()
        if subj_info.patientGender:
            gender_map = {'F': mrd.PatientGender.F, 'M': mrd.PatientGender.M, 'O': mrd.PatientGender.O}
            if subj_info.patientGender in gender_map:
                subject.patient_gender = gender_map[subj_info.patientGender]

        header.subject_information = subject

    # Study information
    if ismrmrd_header.studyInformation:
        study = mrd.StudyInformationType()
        study_info = ismrmrd_header.studyInformation

        if study_info.studyDate:
            study.study_date = study_info.studyDate.to_date()
        if study_info.studyTime:
            study.study_time = mrd.Time.from_time(study_info.studyTime.to_time())
        if study_info.studyID:
            study.study_id = study_info.studyID
        if study_info.accessionNumber:
            study.accession_number = study_info.accessionNumber
        if study_info.referringPhysicianName:
            study.referring_physician_name = study_info.referringPhysicianName
        if study_info.studyDescription:
            study.study_description = study_info.studyDescription
        if study_info.studyInstanceUID:
            study.study_instance_uid = study_info.studyInstanceUID
        if study_info.bodyPartExamined:
            study.body_part_examined = study_info.bodyPartExamined

        header.study_information = study

    # Measurement information
    if ismrmrd_header.measurementInformation:
        meas = mrd.MeasurementInformationType()
        meas_info = ismrmrd_header.measurementInformation

        if meas_info.measurementID:
            meas.measurement_id = meas_info.measurementID
        if meas_info.seriesDate:
            meas.series_date = meas_info.seriesDate.to_date()
        if meas_info.seriesTime:
            meas.series_time = mrd.Time.from_time(meas_info.seriesTime.to_time())
        if meas_info.patientPosition:
            # Map ISMRMRD patient position to MRD
            pos_map = {
                ismrmrd.xsd.patientPositionType.HFS: mrd.PatientPosition.H_FS,
                ismrmrd.xsd.patientPositionType.HFP: mrd.PatientPosition.H_FP,
                ismrmrd.xsd.patientPositionType.HFDR: mrd.PatientPosition.H_FDR,
                ismrmrd.xsd.patientPositionType.HFDL: mrd.PatientPosition.H_FDL,
                ismrmrd.xsd.patientPositionType.FFDR: mrd.PatientPosition.F_FDR,
                ismrmrd.xsd.patientPositionType.FFDL: mrd.PatientPosition.F_FDL,
                ismrmrd.xsd.patientPositionType.FFP: mrd.PatientPosition.F_FP,
                ismrmrd.xsd.patientPositionType.FFS: mrd.PatientPosition.F_FS
            }
            if meas_info.patientPosition in pos_map:
                meas.patient_position = pos_map[meas_info.patientPosition]
        if meas_info.initialSeriesNumber:
            meas.initial_series_number = meas_info.initialSeriesNumber
        if meas_info.protocolName:
            meas.protocol_name = meas_info.protocolName
        if meas_info.seriesDescription:
            meas.series_description = meas_info.seriesDescription
        if meas_info.seriesInstanceUIDRoot:
            meas.series_instance_uid_root = meas_info.seriesInstanceUIDRoot
        if meas_info.frameOfReferenceUID:
            meas.frame_of_reference_uid = meas_info.frameOfReferenceUID
        if meas_info.referencedImageSequence:
            meas.referenced_image_sequence = mrd.ReferencedImageSequenceType()
            for ref_img_uid in meas_info.referencedImageSequence.referencedSOPInstanceUID:
                meas.referenced_image_sequence.referenced_sop_instance_uid.append(ref_img_uid)

        header.measurement_information = meas

    # Acquisition system information
    if ismrmrd_header.acquisitionSystemInformation:
        sys_info = mrd.AcquisitionSystemInformationType()
        acq_sys = ismrmrd_header.acquisitionSystemInformation

        if acq_sys.systemVendor:
            sys_info.system_vendor = acq_sys.systemVendor
        if acq_sys.systemModel:
            sys_info.system_model = acq_sys.systemModel
        if acq_sys.systemFieldStrength_T:
            sys_info.system_field_strength_t = acq_sys.systemFieldStrength_T
        if acq_sys.relativeReceiverNoiseBandwidth:
            sys_info.relative_receiver_noise_bandwidth = acq_sys.relativeReceiverNoiseBandwidth
        if acq_sys.receiverChannels:
            sys_info.receiver_channels = acq_sys.receiverChannels
        if acq_sys.coilLabel:
            for label in acq_sys.coilLabel:
                coil = mrd.CoilLabelType()
                if label.coilNumber:
                    coil.coil_number = label.coilNumber
                if label.coilName:
                    coil.coil_name = label.coilName
                sys_info.coil_label.append(coil)
        if acq_sys.institutionName:
            sys_info.institution_name = acq_sys.institutionName
        if acq_sys.stationName:
            sys_info.station_name = acq_sys.stationName
        if acq_sys.deviceID:
            sys_info.device_id = acq_sys.deviceID
        if acq_sys.deviceSerialNumber:
            sys_info.device_serial_number = acq_sys.deviceSerialNumber

        header.acquisition_system_information = sys_info

    # Experimental conditions
    if ismrmrd_header.experimentalConditions:
        exp = mrd.ExperimentalConditionsType()
        exp_cond = ismrmrd_header.experimentalConditions

        if exp_cond.H1resonanceFrequency_Hz:
            exp.h1resonance_frequency_hz = exp_cond.H1resonanceFrequency_Hz

        header.experimental_conditions = exp

    # Encoding
    if ismrmrd_header.encoding:
        for enc_ismrmrd in ismrmrd_header.encoding:
            enc = mrd.EncodingType()

            # Encoded space
            if enc_ismrmrd.encodedSpace:
                enc_space = mrd.EncodingSpaceType()
                if enc_ismrmrd.encodedSpace.matrixSize:
                    enc_space.matrix_size = mrd.MatrixSizeType(
                        x=enc_ismrmrd.encodedSpace.matrixSize.x,
                        y=enc_ismrmrd.encodedSpace.matrixSize.y,
                        z=enc_ismrmrd.encodedSpace.matrixSize.z
                    )
                if enc_ismrmrd.encodedSpace.fieldOfView_mm:
                    enc_space.field_of_view_mm = mrd.FieldOfViewMm(
                        x=enc_ismrmrd.encodedSpace.fieldOfView_mm.x or 0.0,
                        y=enc_ismrmrd.encodedSpace.fieldOfView_mm.y or 0.0,
                        z=enc_ismrmrd.encodedSpace.fieldOfView_mm.z or 0.0
                    )
                enc.encoded_space = enc_space

            # Recon space
            if enc_ismrmrd.reconSpace:
                recon_space = mrd.EncodingSpaceType()
                if enc_ismrmrd.reconSpace.matrixSize:
                    recon_space.matrix_size = mrd.MatrixSizeType(
                        x=enc_ismrmrd.reconSpace.matrixSize.x,
                        y=enc_ismrmrd.reconSpace.matrixSize.y,
                        z=enc_ismrmrd.reconSpace.matrixSize.z
                    )
                if enc_ismrmrd.reconSpace.fieldOfView_mm:
                    recon_space.field_of_view_mm = mrd.FieldOfViewMm(
                        x=enc_ismrmrd.reconSpace.fieldOfView_mm.x or 0.0,
                        y=enc_ismrmrd.reconSpace.fieldOfView_mm.y or 0.0,
                        z=enc_ismrmrd.reconSpace.fieldOfView_mm.z or 0.0
                    )
                enc.recon_space = recon_space

            # Encoding limits
            if enc_ismrmrd.encodingLimits:
                limits = mrd.EncodingLimitsType()

                if enc_ismrmrd.encodingLimits.kspace_encoding_step_0:
                    lim = enc_ismrmrd.encodingLimits.kspace_encoding_step_0
                    limits.kspace_encoding_step_0 = mrd.LimitType(
                        minimum=lim.minimum, maximum=lim.maximum, center=lim.center
                    )
                if enc_ismrmrd.encodingLimits.kspace_encoding_step_1:
                    lim = enc_ismrmrd.encodingLimits.kspace_encoding_step_1
                    limits.kspace_encoding_step_1 = mrd.LimitType(
                        minimum=lim.minimum, maximum=lim.maximum, center=lim.center
                    )
                if enc_ismrmrd.encodingLimits.kspace_encoding_step_2:
                    lim = enc_ismrmrd.encodingLimits.kspace_encoding_step_2
                    limits.kspace_encoding_step_2 = mrd.LimitType(
                        minimum=lim.minimum, maximum=lim.maximum, center=lim.center
                    )
                if enc_ismrmrd.encodingLimits.average:
                    lim = enc_ismrmrd.encodingLimits.average
                    limits.average = mrd.LimitType(
                        minimum=lim.minimum, maximum=lim.maximum, center=lim.center
                    )
                if enc_ismrmrd.encodingLimits.slice:
                    lim = enc_ismrmrd.encodingLimits.slice
                    limits.slice = mrd.LimitType(
                        minimum=lim.minimum, maximum=lim.maximum, center=lim.center
                    )
                if enc_ismrmrd.encodingLimits.contrast:
                    lim = enc_ismrmrd.encodingLimits.contrast
                    limits.contrast = mrd.LimitType(
                        minimum=lim.minimum, maximum=lim.maximum, center=lim.center
                    )
                if enc_ismrmrd.encodingLimits.phase:
                    lim = enc_ismrmrd.encodingLimits.phase
                    limits.phase = mrd.LimitType(
                        minimum=lim.minimum, maximum=lim.maximum, center=lim.center
                    )
                if enc_ismrmrd.encodingLimits.repetition:
                    lim = enc_ismrmrd.encodingLimits.repetition
                    limits.repetition = mrd.LimitType(
                        minimum=lim.minimum, maximum=lim.maximum, center=lim.center
                    )
                if enc_ismrmrd.encodingLimits.set:
                    lim = enc_ismrmrd.encodingLimits.set
                    limits.set = mrd.LimitType(
                        minimum=lim.minimum, maximum=lim.maximum, center=lim.center
                    )
                if enc_ismrmrd.encodingLimits.segment:
                    lim = enc_ismrmrd.encodingLimits.segment
                    limits.segment = mrd.LimitType(
                        minimum=lim.minimum, maximum=lim.maximum, center=lim.center
                    )

                enc.encoding_limits = limits

            # Trajectory
            if enc_ismrmrd.trajectory:
                traj_map = {
                    ismrmrd.xsd.trajectoryType.CARTESIAN: mrd.Trajectory.CARTESIAN,
                    ismrmrd.xsd.trajectoryType.EPI: mrd.Trajectory.EPI,
                    ismrmrd.xsd.trajectoryType.RADIAL: mrd.Trajectory.RADIAL,
                    ismrmrd.xsd.trajectoryType.GOLDENANGLE: mrd.Trajectory.GOLDENANGLE,
                    ismrmrd.xsd.trajectoryType.SPIRAL: mrd.Trajectory.SPIRAL,
                    ismrmrd.xsd.trajectoryType.OTHER: mrd.Trajectory.OTHER
                }
                if enc_ismrmrd.trajectory in traj_map:
                    enc.trajectory = traj_map[enc_ismrmrd.trajectory]

            # Trajectory description (if present)
            if enc_ismrmrd.trajectoryDescription:
                traj_desc = mrd.TrajectoryDescriptionType()
                if enc_ismrmrd.trajectoryDescription.identifier:
                    traj_desc.identifier = enc_ismrmrd.trajectoryDescription.identifier
                # Add more trajectory description fields as needed
                enc.trajectory_description = traj_desc

            # Parallel imaging
            if enc_ismrmrd.parallelImaging:
                parallel = mrd.ParallelImagingType()
                par_img = enc_ismrmrd.parallelImaging

                if par_img.accelerationFactor:
                    acc = mrd.AccelerationFactorType()
                    if par_img.accelerationFactor.kspace_encoding_step_1:
                        acc.kspace_encoding_step_1 = par_img.accelerationFactor.kspace_encoding_step_1
                    if par_img.accelerationFactor.kspace_encoding_step_2:
                        acc.kspace_encoding_step_2 = par_img.accelerationFactor.kspace_encoding_step_2
                    parallel.acceleration_factor = acc

                if par_img.calibrationMode:
                    calib_map = {
                        ismrmrd.xsd.calibrationModeType.EMBEDDED: mrd.CalibrationMode.EMBEDDED,
                        ismrmrd.xsd.calibrationModeType.INTERLEAVED: mrd.CalibrationMode.INTERLEAVED,
                        ismrmrd.xsd.calibrationModeType.SEPARATE: mrd.CalibrationMode.SEPARATE,
                        ismrmrd.xsd.calibrationModeType.EXTERNAL: mrd.CalibrationMode.EXTERNAL,
                        ismrmrd.xsd.calibrationModeType.OTHER: mrd.CalibrationMode.OTHER
                    }
                    if par_img.calibrationMode in calib_map:
                        parallel.calibration_mode = calib_map[par_img.calibrationMode]

                if par_img.interleavingDimension:
                    interleave_map = {
                        ismrmrd.xsd.interleavingDimensionType.PHASE: mrd.InterleavingDimension.PHASE,
                        ismrmrd.xsd.interleavingDimensionType.REPETITION: mrd.InterleavingDimension.REPETITION,
                        ismrmrd.xsd.interleavingDimensionType.CONTRAST: mrd.InterleavingDimension.CONTRAST,
                        ismrmrd.xsd.interleavingDimensionType.AVERAGE: mrd.InterleavingDimension.AVERAGE,
                        ismrmrd.xsd.interleavingDimensionType.OTHER: mrd.InterleavingDimension.OTHER
                    }
                    if par_img.interleavingDimension in interleave_map:
                        parallel.interleaving_dimension = interleave_map[par_img.interleavingDimension]

                enc.parallel_imaging = parallel

            # Echo train length
            if enc_ismrmrd.echoTrainLength:
                enc.echo_train_length = enc_ismrmrd.echoTrainLength

            header.encoding.append(enc)

    # Sequence parameters
    if ismrmrd_header.sequenceParameters:
        seq = mrd.SequenceParametersType()
        seq_params = ismrmrd_header.sequenceParameters

        if seq_params.TR:
            for tr in seq_params.TR:
                seq.t_r.append(tr)
        if seq_params.TE:
            for te in seq_params.TE:
                seq.t_e.append(te)
        if seq_params.TI:
            for ti in seq_params.TI:
                seq.t_i.append(ti)
        if seq_params.flipAngle_deg:
            for fa in seq_params.flipAngle_deg:
                seq.flip_angle_deg.append(fa)
        if seq_params.sequence_type:
            seq.sequence_type = seq_params.sequence_type
        if seq_params.echo_spacing:
            for es in seq_params.echo_spacing:
                seq.echo_spacing.append(es)

        header.sequence_parameters = seq

    # User parameters
    if ismrmrd_header.userParameters:
        user_params = mrd.UserParametersType()
        for param in ismrmrd_header.userParameters.userParameterLong:
            user_param = mrd.UserParameterLongType()
            user_param.name = param.name or ""
            user_param.value = param.value or 0
            user_params.user_parameter_long.append(user_param)

        for param in ismrmrd_header.userParameters.userParameterDouble:
            user_param = mrd.UserParameterDoubleType()
            user_param.name = param.name or ""
            user_param.value = param.value or 0.0
            user_params.user_parameter_double.append(user_param)

        for param in ismrmrd_header.userParameters.userParameterString:
            user_param = mrd.UserParameterStringType()
            user_param.name = param.name or ""
            user_param.value = param.value or ""
            user_params.user_parameter_string.append(user_param)

        for param in ismrmrd_header.userParameters.userParameterBase64:
            user_param = mrd.UserParameterBase64Type()
            user_param.name = param.name or ""
            user_param.value = str(param.value)
            user_params.user_parameter_base64.append(user_param)

        header.user_parameters = user_params

    return header


def convert_acquisition(ismrmrd_acq: ismrmrd.Acquisition) -> mrd.Acquisition:
    """Convert ISMRMRD acquisition to MRD acquisition."""
    acq = mrd.Acquisition()

    header = ismrmrd_acq.getHead()
    acq.head.flags = mrd.AcquisitionFlags(ismrmrd_acq.flags)
    acq.head.idx.kspace_encode_step_1 = header.idx.kspace_encode_step_1
    acq.head.idx.kspace_encode_step_2 = header.idx.kspace_encode_step_2
    acq.head.idx.average = header.idx.average
    acq.head.idx.slice = header.idx.slice
    acq.head.idx.contrast = header.idx.contrast
    acq.head.idx.phase = header.idx.phase
    acq.head.idx.repetition = header.idx.repetition
    acq.head.idx.set = header.idx.set
    acq.head.idx.segment = header.idx.segment
    acq.head.measurement_uid = header.measurement_uid
    acq.head.scan_counter = header.scan_counter
    acq.head.acquisition_time_stamp_ns = int(header.acquisition_time_stamp * 1e6)   # ms to ns
    acq.head.physiology_time_stamp_ns = [int(ts * 1e6) for ts in header.physiology_time_stamp]  # ms to ns
    acq.head.channel_order = list(range(header.active_channels))
    acq.head.discard_pre = header.discard_pre
    acq.head.discard_post = header.discard_post
    acq.head.center_sample = header.center_sample
    acq.head.encoding_space_ref = header.encoding_space_ref
    acq.head.sample_time_ns = int(header.sample_time_us * 1000) # us to ns
    acq.head.position[:] = header.position
    acq.head.read_dir[:] = header.read_dir
    acq.head.phase_dir[:] = header.phase_dir
    acq.head.slice_dir[:] = header.slice_dir
    acq.head.patient_table_position[:] = header.patient_table_position
    acq.head.user_int = [0] * ismrmrd.USER_INTS
    acq.head.user_float = [0.0] * ismrmrd.USER_FLOATS
    for i in range(ismrmrd.USER_INTS):
        acq.head.user_int[i] = header.user_int[i]
    for i in range(ismrmrd.USER_FLOATS):
        acq.head.user_float[i] = header.user_float[i]

    acq.data = ismrmrd_acq.data.copy()

    if ismrmrd_acq.traj is not None and ismrmrd_acq.traj.size > 0:
        acq.trajectory = ismrmrd_acq.traj.copy()

    return acq


def convert_waveform(ismrmrd_wfm: ismrmrd.Waveform) -> mrd.WaveformUint32:
    """Convert ISMRMRD waveform to MRD waveform."""
    header = ismrmrd_wfm.getHead()
    return mrd.WaveformUint32(
        flags = ismrmrd_wfm.flags,
        measurement_uid = header.measurement_uid,
        scan_counter = header.scan_counter,
        time_stamp_ns = int(header.time_stamp * 1e6), # ms to ns
        sample_time_ns = int(header.sample_time_us * 1000), # us to ns
        waveform_id = header.waveform_id,
        data = ismrmrd_wfm.data.copy()
    )


def convert_image(ismrmrd_img: ismrmrd.Image) -> mrd.StreamItem:
    """Convert ISMRMRD image to MRD image StreamItem."""
    in_head = ismrmrd_img.getHead()
    out_head = mrd.ImageHeader(image_type=mrd.ImageType(in_head.image_type))

    # Copy header fields
    out_head.flags = mrd.ImageFlags(in_head.flags)
    out_head.measurement_uid = in_head.measurement_uid
    out_head.field_of_view[:] = in_head.field_of_view
    out_head.position[:] = in_head.position
    out_head.col_dir[:] = in_head.read_dir
    out_head.line_dir[:] = in_head.phase_dir
    out_head.slice_dir[:] = in_head.slice_dir
    out_head.patient_table_position[:] = in_head.patient_table_position
    out_head.average = in_head.average
    out_head.slice = in_head.slice
    out_head.contrast = in_head.contrast
    out_head.phase = in_head.phase
    out_head.repetition = in_head.repetition
    out_head.set = in_head.set
    out_head.acquisition_time_stamp_ns = int(in_head.acquisition_time_stamp * 1e6) # ms to ns
    out_head.physiology_time_stamp_ns = [int(ts * 1e6) for ts in in_head.physiology_time_stamp]  # ms to ns
    out_head.image_index = in_head.image_index
    out_head.image_series_index = in_head.image_series_index
    out_head.user_int = [0] * ismrmrd.USER_INTS
    out_head.user_float = [0.0] * ismrmrd.USER_FLOATS
    for i in range(ismrmrd.USER_INTS):
        out_head.user_int[i] = in_head.user_int[i]
    for i in range(ismrmrd.USER_FLOATS):
        out_head.user_float[i] = in_head.user_float[i]

    # Handle meta/attribute_string conversion
    meta = {}
    if ismrmrd_img.attribute_string:
        try:
            # Parse the ISMRMRD Meta XML string
            ismrmrd_meta = ismrmrd.Meta.deserialize(ismrmrd_img.attribute_string)

            # Convert to MRD ImageMeta format: dict[str, list[ImageMetaValue]]
            for key, value in ismrmrd_meta.items():
                # Ensure value is a list
                values_list = value if isinstance(value, list) else [value]

                # Convert each value to ImageMetaValue
                meta_values = []
                for v in values_list:
                    # ISMRMRD Meta deserializes everything as strings
                    # Try to convert to appropriate numeric type if possible
                    if not isinstance(v, str):
                        # Already a typed value (shouldn't happen with ISMRMRD, but handle it)
                        if isinstance(v, (int, np.integer)):
                            meta_values.append(mrd.ImageMetaValue.Int64(int(v)))
                        elif isinstance(v, (float, np.floating)):
                            meta_values.append(mrd.ImageMetaValue.Float64(float(v)))
                        else:
                            meta_values.append(mrd.ImageMetaValue.String(str(v)))
                    else:
                        # Try to parse numeric strings
                        str_val = v.strip()

                        # Try integer first
                        try:
                            int_val = int(str_val)
                            # Check if it's actually an integer (not a float like "3.0")
                            if '.' not in str_val and 'e' not in str_val.lower():
                                meta_values.append(mrd.ImageMetaValue.Int64(int_val))
                                continue
                        except (ValueError, TypeError):
                            pass

                        # Try float
                        try:
                            float_val = float(str_val)
                            meta_values.append(mrd.ImageMetaValue.Float64(float_val))
                            continue
                        except (ValueError, TypeError):
                            pass

                        # Fall back to string
                        meta_values.append(mrd.ImageMetaValue.String(str_val))

                meta[key] = meta_values
        except Exception:
            # If parsing fails, skip meta
            pass

    data = ismrmrd_img.data
    dtype = data.dtype
    if dtype == np.uint16:
        img = mrd.Image[np.uint16](head=out_head, data=data.astype(np.uint16), meta=meta)
        return mrd.StreamItem.ImageUint16(img)
    elif dtype == np.int16:
        img = mrd.Image[np.int16](head=out_head, data=data.astype(np.int16), meta=meta)
        return mrd.StreamItem.ImageInt16(img)
    elif dtype == np.uint32:
        img = mrd.Image[np.uint32](head=out_head, data=data.astype(np.uint32), meta=meta)
        return mrd.StreamItem.ImageUint32(img)
    elif dtype == np.int32:
        img = mrd.Image[np.int32](head=out_head, data=data.astype(np.int32), meta=meta)
        return mrd.StreamItem.ImageInt32(img)
    elif dtype == np.float32:
        img = mrd.Image[np.float32](head=out_head, data=data.astype(np.float32), meta=meta)
        return mrd.StreamItem.ImageFloat(img)
    elif dtype == np.float64:
        img = mrd.Image[np.float64](head=out_head, data=data.astype(np.float64), meta=meta)
        return mrd.StreamItem.ImageDouble(img)
    elif dtype == np.complex64:
        img = mrd.Image[np.complex64](head=out_head, data=data.astype(np.complex64), meta=meta)
        return mrd.StreamItem.ImageComplexFloat(img)
    elif dtype == np.complex128:
        img = mrd.Image[np.complex128](head=out_head, data=data.astype(np.complex128), meta=meta)
        return mrd.StreamItem.ImageComplexDouble(img)
    else:
        raise ValueError(f"Unsupported image data type: {dtype}")


def _generate_mrd_stream_items(ismrmrd_items):
    """
    Generator that yields MRD StreamItems from ISMRMRD items.

    Args:
        ismrmrd_items: Iterable of ISMRMRD items (from deserializer)

    Yields:
        MRD StreamItem objects
    """
    for item in ismrmrd_items:
        # Skip header - it's handled separately
        if isinstance(item, ismrmrd.xsd.ismrmrdHeader):
            continue
        elif isinstance(item, ismrmrd.Acquisition):
            mrd_acq = convert_acquisition(item)
            yield mrd.StreamItem.Acquisition(mrd_acq)
        elif isinstance(item, ismrmrd.Waveform):
            mrd_wfm = convert_waveform(item)
            yield mrd.StreamItem.WaveformUint32(mrd_wfm)
        elif isinstance(item, ismrmrd.Image):
            mrd_img_item = convert_image(item)
            yield mrd_img_item
        # Skip other types (text, ndarray) for now
        else:
            pass


def convert_ismrmrd_to_mrd(input_stream: BinaryIO, output_stream: BinaryIO) -> None:
    """
    Convert ISMRMRD stream to MRD stream.

    Args:
        input_stream: Binary input stream containing ISMRMRD data
        output_stream: Binary output stream for MRD data
    """
    # Create ISMRMRD deserializer and MRD writer
    with ismrmrd.serialization.ProtocolDeserializer(input_stream) as deserializer:
        with mrd.BinaryMrdWriter(output_stream) as writer:
            items = deserializer.deserialize()

            # Check if first item is a header
            first_item = next(items, None)
            if first_item is None:
                # Empty stream
                writer.write_header(None)
                items = iter([])
            elif isinstance(first_item, ismrmrd.xsd.ismrmrdHeader):
                # Convert and write the header
                mrd_header = convert_header(first_item)
                writer.write_header(mrd_header)
            else:
                writer.write_header(None)
                # Chain this item back with the rest
                items = itertools.chain([first_item], items)

            # Convert and write all data items using generator
            writer.write_data(_generate_mrd_stream_items(items))


def main():
    parser = argparse.ArgumentParser(
        description="Convert ISMRMRD stream to MRD stream"
    )
    parser.add_argument(
        '-i', '--input',
        type=str,
        help="Input ISMRMRD stream (default: stdin)"
    )
    parser.add_argument(
        '-o', '--output',
        type=str,
        help="Output MRD stream (default: stdout)"
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
        convert_ismrmrd_to_mrd(input_stream, output_stream)
        return 0
    finally:
        if args.input:
            input_stream.close()
        if args.output:
            output_stream.close()


if __name__ == "__main__":
    sys.exit(main())

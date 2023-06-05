#include "generated/binary/protocols.h"
#include <filesystem>
#include <iostream>
#include <exception>
#include <ismrmrd/dataset.h>
#include <ismrmrd/meta.h>
#include <ismrmrd/serialization_iostream.h>
#include <ismrmrd/xml.h>
#include <ismrmrd/version.h>
#include <xtensor/xview.hpp>

std::string date_to_string(const yardl::Date &d)
{
    std::stringstream ss;
    ss << date::format("%F", d);
    return ss.str();
}

std::string time_to_string(const yardl::Time &t)
{
    std::stringstream ss;
    ss << date::format("%T", t);
    return ss.str();
};

// Convert mrd::SubjectInformationType to ISMRMRD::SubjectInformation
ISMRMRD::SubjectInformation convert(mrd::SubjectInformationType &subjectInformation)
{
    ISMRMRD::SubjectInformation s;
    if (subjectInformation.patient_name)
    {
        s.patientName = *subjectInformation.patient_name;
    }

    if (subjectInformation.patient_weight_kg)
    {
        s.patientWeight_kg = *subjectInformation.patient_weight_kg;
    }

    if (subjectInformation.patient_height_m)
    {
        s.patientHeight_m = *subjectInformation.patient_height_m;
    }

    if (subjectInformation.patient_id)
    {
        s.patientID = *subjectInformation.patient_id;
    }

    if (subjectInformation.patient_birthdate)
    {
        s.patientBirthdate = date_to_string(*subjectInformation.patient_birthdate);
    }

    if (subjectInformation.patient_gender)
    {
        if (*subjectInformation.patient_gender == mrd::PatientGender::kF)
        {
            s.patientGender = "F";
        }
        else if (*subjectInformation.patient_gender == mrd::PatientGender::kM)
        {
            s.patientGender = "M";
        }
        else if (*subjectInformation.patient_gender == mrd::PatientGender::kO)
        {
            s.patientGender = "O";
        }
        else
        {
            throw std::runtime_error("Unknown gender");
        }
    }

    return s;
}

// Convert mrd::StudyInformationType to ISMRMRD::StudyInformation
ISMRMRD::StudyInformation convert(mrd::StudyInformationType &studyInformation)
{
    ISMRMRD::StudyInformation s;

    if (studyInformation.study_date)
    {
        s.studyDate = date_to_string(*studyInformation.study_date);
    }

    if (studyInformation.study_time)
    {
        s.studyTime = time_to_string(*studyInformation.study_time);
    }

    if (studyInformation.study_id)
    {
        s.studyID = *studyInformation.study_id;
    }

    if (studyInformation.accession_number)
    {
        s.accessionNumber = *studyInformation.accession_number;
    }

    if (studyInformation.referring_physician_name)
    {
        s.referringPhysicianName = *studyInformation.referring_physician_name;
    }

    if (studyInformation.study_description)
    {
        s.studyDescription = *studyInformation.study_description;
    }

    if (studyInformation.study_instance_uid)
    {
        s.studyInstanceUID = *studyInformation.study_instance_uid;
    }

    if (studyInformation.body_part_examined)
    {
        s.bodyPartExamined = *studyInformation.body_part_examined;
    }

    return s;
}

// Convert mrd::PatientPosition to ISMRMRD patient position string
std::string patient_position_to_string(mrd::PatientPosition &p)
{
    if (p == mrd::PatientPosition::kHFP)
    {
        return "HFP";
    }
    else if (p == mrd::PatientPosition::kHFS)
    {
        return "HFS";
    }
    else if (p == mrd::PatientPosition::kHFDR)
    {
        return "HFDR";
    }
    else if (p == mrd::PatientPosition::kHFDL)
    {
        return "HFDL";
    }
    else if (p == mrd::PatientPosition::kFFP)
    {
        return "FFP";
    }
    else if (p == mrd::PatientPosition::kFFS)
    {
        return "FFS";
    }
    else if (p == mrd::PatientPosition::kFFDR)
    {
        return "FFDR";
    }
    else if (p == mrd::PatientPosition::kFFDL)
    {
        return "FFDL";
    }
    else
    {
        throw std::runtime_error("Unknown Patient Position");
    }
}

// Convert mrd::ThreeDimensionalFloat to ISMRMRD::threeDimensionalFloat
ISMRMRD::threeDimensionalFloat convert(mrd::ThreeDimensionalFloat &threeDimensionalFloat)
{
    ISMRMRD::threeDimensionalFloat t;
    t.x = threeDimensionalFloat.x;
    t.y = threeDimensionalFloat.y;
    t.z = threeDimensionalFloat.z;
    return t;
}

// Convert mrd::MeasurementDependencyType to ISMRMRD::MeasurementDependency
ISMRMRD::MeasurementDependency convert(mrd::MeasurementDependencyType &measurementDependency)
{
    ISMRMRD::MeasurementDependency m;
    m.measurementID = measurementDependency.measurement_id;
    m.dependencyType = measurementDependency.dependency_type;
    return m;
}

// Convert mrd::MeasurementInformationType to ISMRMRD::MeasurementInformation
ISMRMRD::MeasurementInformation convert(mrd::MeasurementInformationType &measurementInformation)
{
    ISMRMRD::MeasurementInformation m;

    if (measurementInformation.measurement_id)
    {
        m.measurementID = *measurementInformation.measurement_id;
    }

    if (measurementInformation.series_date)
    {
        m.seriesDate = date_to_string(*measurementInformation.series_date);
    }

    if (measurementInformation.series_time)
    {
        m.seriesTime = time_to_string(*measurementInformation.series_time);
    }

    m.patientPosition = patient_position_to_string(measurementInformation.patient_position);

    if (measurementInformation.relative_table_position)
    {
        m.relativeTablePosition = convert(*measurementInformation.relative_table_position);
    }

    if (measurementInformation.initial_series_number)
    {
        m.initialSeriesNumber = *measurementInformation.initial_series_number;
    }

    if (measurementInformation.protocol_name)
    {
        m.protocolName = *measurementInformation.protocol_name;
    }

    if (measurementInformation.sequence_name)
    {
        m.sequenceName = *measurementInformation.sequence_name;
    }

    if (measurementInformation.series_description)
    {
        m.seriesDescription = *measurementInformation.series_description;
    }

    for (auto &dependency : measurementInformation.measurement_dependency)
    {
        m.measurementDependency.push_back(convert(dependency));
    }

    if (measurementInformation.series_instance_uid_root)
    {
        m.seriesInstanceUIDRoot = *measurementInformation.series_instance_uid_root;
    }

    if (measurementInformation.frame_of_reference_uid)
    {
        m.frameOfReferenceUID = *measurementInformation.frame_of_reference_uid;
    }

    if (measurementInformation.referenced_image_sequence)
    {
        for (auto &image : measurementInformation.referenced_image_sequence->referenced_sop_instance_uid)
        {
            ISMRMRD::ReferencedImageSequence referencedImage;
            referencedImage.referencedSOPInstanceUID = image;
            m.referencedImageSequence.push_back(referencedImage);
        }
    }

    return m;
}

// Convert mrd::AcquisitionSystemInformationType to ISMRMRD::AcquisitionSystemInformation
ISMRMRD::AcquisitionSystemInformation convert(mrd::AcquisitionSystemInformationType &a)
{
    ISMRMRD::AcquisitionSystemInformation asi;

    if (a.system_vendor)
    {
        asi.systemVendor = *a.system_vendor;
    }

    if (a.system_model)
    {
        asi.systemModel = *a.system_model;
    }

    if (a.system_field_strength_t)
    {
        asi.systemFieldStrength_T = *a.system_field_strength_t;
    }

    if (a.relative_receiver_noise_bandwidth)
    {
        asi.relativeReceiverNoiseBandwidth = *a.relative_receiver_noise_bandwidth;
    }

    if (a.receiver_channels)
    {
        asi.receiverChannels = *a.receiver_channels;
    }

    if (a.coil_label.size() > 0)
    {
        for (auto &c : a.coil_label)
        {
            ISMRMRD::CoilLabel cl;
            cl.coilName = c.coil_name;
            cl.coilNumber = c.coil_number;
            asi.coilLabel.push_back(cl);
        }
    }

    if (a.institution_name)
    {
        asi.institutionName = *a.institution_name;
    }

    if (a.station_name)
    {
        asi.stationName = *a.station_name;
    }

    if (a.device_id)
    {
        asi.deviceID = *a.device_id;
    }

    if (a.device_serial_number)
    {
        asi.deviceSerialNumber = *a.device_serial_number;
    }

    return asi;
}

// Convert mrd::ExperimentalConditionsType to ISMRMRD::ExperimentalConditions
ISMRMRD::ExperimentalConditions convert(mrd::ExperimentalConditionsType &e)
{
    ISMRMRD::ExperimentalConditions ec;
    ec.H1resonanceFrequency_Hz = e.h1resonance_frequency_hz;
    return ec;
}

// Convert mrd::MatrixSizeType to ISMRMRD::MatrixSize
ISMRMRD::MatrixSize convert(mrd::MatrixSizeType &m)
{
    ISMRMRD::MatrixSize matrixSize;
    matrixSize.x = m.x;
    matrixSize.y = m.y;
    matrixSize.z = m.z;
    return matrixSize;
}

// Convert mrd::FieldOfViewmm to ISMRMRD::FieldOfView_mm
ISMRMRD::FieldOfView_mm convert(mrd::FieldOfViewMm &f)
{
    ISMRMRD::FieldOfView_mm fieldOfView;
    fieldOfView.x = f.x;
    fieldOfView.y = f.y;
    fieldOfView.z = f.z;
    return fieldOfView;
}

// Convert mrd::EncodingSpaceType to ISMRMRD::EncodingSpace
ISMRMRD::EncodingSpace convert(mrd::EncodingSpaceType &e)
{
    ISMRMRD::EncodingSpace encodingSpace;
    encodingSpace.matrixSize = convert(e.matrix_size);
    encodingSpace.fieldOfView_mm = convert(e.field_of_view_mm);
    return encodingSpace;
}

// Convert mrd::LimitType to ISMRMRD::Limit
ISMRMRD::Limit convert(mrd::LimitType &l)
{
    ISMRMRD::Limit limit;
    limit.minimum = l.minimum;
    limit.maximum = l.maximum;
    limit.center = l.center;
    return limit;
}

// Convert mrd::EncodingLimitsType to ISMRMRD::EncodingLimits
ISMRMRD::EncodingLimits convert(mrd::EncodingLimitsType &encodingLimit)
{
    ISMRMRD::EncodingLimits el;

    if (encodingLimit.kspace_encoding_step_0)
    {
        el.kspace_encoding_step_0 = convert(*encodingLimit.kspace_encoding_step_0);
    }

    if (encodingLimit.kspace_encoding_step_1)
    {
        el.kspace_encoding_step_1 = convert(*encodingLimit.kspace_encoding_step_1);
    }

    if (encodingLimit.kspace_encoding_step_2)
    {
        el.kspace_encoding_step_2 = convert(*encodingLimit.kspace_encoding_step_2);
    }

    if (encodingLimit.average)
    {
        el.average = convert(*encodingLimit.average);
    }

    if (encodingLimit.slice)
    {
        el.slice = convert(*encodingLimit.slice);
    }

    if (encodingLimit.contrast)
    {
        el.contrast = convert(*encodingLimit.contrast);
    }

    if (encodingLimit.phase)
    {
        el.phase = convert(*encodingLimit.phase);
    }

    if (encodingLimit.repetition)
    {
        el.repetition = convert(*encodingLimit.repetition);
    }

    if (encodingLimit.set)
    {
        el.set = convert(*encodingLimit.set);
    }

    if (encodingLimit.segment)
    {
        el.segment = convert(*encodingLimit.segment);
    }

    if (encodingLimit.user_0)
    {
        el.user[0] = convert(*encodingLimit.user_0);
    }

    if (encodingLimit.user_1)
    {
        el.user[1] = convert(*encodingLimit.user_1);
    }

    if (encodingLimit.user_2)
    {
        el.user[2] = convert(*encodingLimit.user_2);
    }

    if (encodingLimit.user_3)
    {
        el.user[3] = convert(*encodingLimit.user_3);
    }

    if (encodingLimit.user_4)
    {
        el.user[4] = convert(*encodingLimit.user_4);
    }

    if (encodingLimit.user_5)
    {
        el.user[5] = convert(*encodingLimit.user_5);
    }

    if (encodingLimit.user_6)
    {
        el.user[6] = convert(*encodingLimit.user_6);
    }

    if (encodingLimit.user_7)
    {
        el.user[7] = convert(*encodingLimit.user_7);
    }

    return el;
}

// Convert mrd::UserParameterLongType to ISMRMRD::UserParameterLong
ISMRMRD::UserParameterLong convert(mrd::UserParameterLongType &u)
{
    ISMRMRD::UserParameterLong userParameterLong;
    userParameterLong.name = u.name;
    userParameterLong.value = u.value;
    return userParameterLong;
}

// Convert mrd::UserParameterDoubleType to ISMRMRD::UserParameterDouble
ISMRMRD::UserParameterDouble convert(mrd::UserParameterDoubleType &u)
{
    ISMRMRD::UserParameterDouble userParameterDouble;
    userParameterDouble.name = u.name;
    userParameterDouble.value = u.value;
    return userParameterDouble;
}

// Convert mrd::UserParameterStringType to ISMRMRD::UserParameterString
ISMRMRD::UserParameterString convert(mrd::UserParameterStringType &u)
{
    ISMRMRD::UserParameterString userParameterString;
    userParameterString.name = u.name;
    userParameterString.value = u.value;
    return userParameterString;
}

// Convert mrd::TrajectoryDescriptionType to ISMRMRD::TrajectoryDescription
ISMRMRD::TrajectoryDescription convert(mrd::TrajectoryDescriptionType &t)
{
    ISMRMRD::TrajectoryDescription trajectoryDescription;
    trajectoryDescription.identifier = t.identifier;

    for (auto &u : t.user_parameter_long)
    {
        trajectoryDescription.userParameterLong.push_back(convert(u));
    }

    for (auto &u : t.user_parameter_double)
    {
        trajectoryDescription.userParameterDouble.push_back(convert(u));
    }

    for (auto &u : t.user_parameter_string)
    {
        trajectoryDescription.userParameterString.push_back(convert(u));
    }

    if (t.comment)
    {
        trajectoryDescription.comment = *t.comment;
    }

    return trajectoryDescription;
}

// Convert mrd::AccelerationFactorType to ISMRMRD::AccelerationFactor
ISMRMRD::AccelerationFactor convert(mrd::AccelerationFactorType &a)
{
    ISMRMRD::AccelerationFactor accelerationFactor;
    accelerationFactor.kspace_encoding_step_1 = a.kspace_encoding_step_1;
    accelerationFactor.kspace_encoding_step_2 = a.kspace_encoding_step_2;
    return accelerationFactor;
}

// Convert mrd::CalibrationMode to ISMRMRD calibration mode string
std::string calibration_mode_to_string(mrd::CalibrationMode &m)
{
    switch (m)
    {
    case mrd::CalibrationMode::kEmbedded:
        return "embedded";
    case mrd::CalibrationMode::kInterleaved:
        return "interleaved";
    case mrd::CalibrationMode::kSeparate:
        return "separate";
    case mrd::CalibrationMode::kExternal:
        return "external";
    case mrd::CalibrationMode::kOther:
        return "other";
    default:
        throw std::runtime_error("Unknown CalibrationMode: " + std::to_string((int)m));
    }
}

// Convert mrd::InterleavingDimension to ISMRMRD interleaving dimension string
std::string interleaving_dimension_to_string(mrd::InterleavingDimension &d)
{
    switch (d)
    {
    case mrd::InterleavingDimension::kPhase:
        return "phase";
    case mrd::InterleavingDimension::kRepetition:
        return "repetition";
    case mrd::InterleavingDimension::kContrast:
        return "contrast";
    case mrd::InterleavingDimension::kAverage:
        return "average";
    case mrd::InterleavingDimension::kOther:
        return "other";
    default:
        throw std::runtime_error("Unknown InterleavingDimension: " + std::to_string((int)d));
    }
}

// Convert mrd::MultibandSpacingType to ISMRMRD::MultibandSpacing
ISMRMRD::MultibandSpacing convert(mrd::MultibandSpacingType &m)
{
    ISMRMRD::MultibandSpacing multibandSpacing;
    for (auto s : m.d_z)
    {
        multibandSpacing.dZ.push_back(s);
    }
    return multibandSpacing;
}

// Convert mrd::Calibration to ISMRMRD::MultibandCalibrationType
ISMRMRD::MultibandCalibrationType convert(mrd::Calibration &m)
{
    switch (m)
    {
    case mrd::Calibration::kSeparable2D:
        return ISMRMRD::MultibandCalibrationType::SEPARABLE2D;
    case mrd::Calibration::kFull3D:
        return ISMRMRD::MultibandCalibrationType::FULL3D;
    case mrd::Calibration::kOther:
        return ISMRMRD::MultibandCalibrationType::OTHER;
    default:
        throw std::runtime_error("Unknown Calibration: " + std::to_string((int)m));
    }
}

// Convert mrd::MultibandType to ISMRMRD::Multiband
ISMRMRD::Multiband convert(mrd::MultibandType &m)
{
    ISMRMRD::Multiband multiband;
    for (auto s : m.spacing)
    {
        multiband.spacing.push_back(convert(s));
    }
    multiband.deltaKz = m.delta_kz;
    multiband.multiband_factor = m.multiband_factor;
    multiband.calibration = convert(m.calibration);
    multiband.calibration_encoding = m.calibration_encoding;
    return multiband;
}

// Convert mrd::ParallelImagingType to ISMRMRD::ParallelImaging
ISMRMRD::ParallelImaging convert(mrd::ParallelImagingType &p)
{
    ISMRMRD::ParallelImaging parallelImaging;
    parallelImaging.accelerationFactor = convert(p.acceleration_factor);
    if (p.calibration_mode)
    {
        parallelImaging.calibrationMode = calibration_mode_to_string(*p.calibration_mode);
    }
    if (p.interleaving_dimension)
    {
        parallelImaging.interleavingDimension = interleaving_dimension_to_string(*p.interleaving_dimension);
    }
    if (p.multiband)
    {
        parallelImaging.multiband = convert(*p.multiband);
    }
    return parallelImaging;
}

// Convert mrd::EncodingType to ISMRMRD::Encoding
ISMRMRD::Encoding convert(mrd::EncodingType &e)
{
    ISMRMRD::Encoding encoding;

    encoding.encodedSpace = convert(e.encoded_space);
    encoding.reconSpace = convert(e.recon_space);
    encoding.encodingLimits = convert(e.encoding_limits);

    switch (e.trajectory)
    {
    case mrd::Trajectory::kCartesian:
        encoding.trajectory = ISMRMRD::TrajectoryType::CARTESIAN;
        break;
    case mrd::Trajectory::kEpi:
        encoding.trajectory = ISMRMRD::TrajectoryType::EPI;
        break;
    case mrd::Trajectory::kRadial:
        encoding.trajectory = ISMRMRD::TrajectoryType::RADIAL;
        break;
    case mrd::Trajectory::kGoldenangle:
        encoding.trajectory = ISMRMRD::TrajectoryType::GOLDENANGLE;
        break;
    case mrd::Trajectory::kSpiral:
        encoding.trajectory = ISMRMRD::TrajectoryType::SPIRAL;
        break;
    case mrd::Trajectory::kOther:
        encoding.trajectory = ISMRMRD::TrajectoryType::OTHER;
        break;
    default:
        throw std::runtime_error("Unknown Trajectory: " + std::to_string((int)e.trajectory));
    }

    if (e.trajectory_description)
    {
        encoding.trajectoryDescription = convert(*e.trajectory_description);
    }

    if (e.parallel_imaging)
    {
        encoding.parallelImaging = convert(*e.parallel_imaging);
    }

    if (e.echo_train_length)
    {
        encoding.echoTrainLength = *e.echo_train_length;
    }

    return encoding;
}

// Convert mrd::DiffusionDimension to ISMRMRD::DiffusionDimension
ISMRMRD::DiffusionDimension convert(mrd::DiffusionDimension &diffusionDimension)
{
    switch (diffusionDimension)
    {
    case mrd::DiffusionDimension::kAverage:
        return ISMRMRD::DiffusionDimension::AVERAGE;
    case mrd::DiffusionDimension::kContrast:
        return ISMRMRD::DiffusionDimension::CONTRAST;
    case mrd::DiffusionDimension::kPhase:
        return ISMRMRD::DiffusionDimension::PHASE;
    case mrd::DiffusionDimension::kRepetition:
        return ISMRMRD::DiffusionDimension::REPETITION;
    case mrd::DiffusionDimension::kSegment:
        return ISMRMRD::DiffusionDimension::SEGMENT;
    case mrd::DiffusionDimension::kSet:
        return ISMRMRD::DiffusionDimension::SET;
    case mrd::DiffusionDimension::kUser0:
        return ISMRMRD::DiffusionDimension::USER_0;
    case mrd::DiffusionDimension::kUser1:
        return ISMRMRD::DiffusionDimension::USER_1;
    case mrd::DiffusionDimension::kUser2:
        return ISMRMRD::DiffusionDimension::USER_2;
    case mrd::DiffusionDimension::kUser3:
        return ISMRMRD::DiffusionDimension::USER_3;
    case mrd::DiffusionDimension::kUser4:
        return ISMRMRD::DiffusionDimension::USER_4;
    case mrd::DiffusionDimension::kUser5:
        return ISMRMRD::DiffusionDimension::USER_5;
    case mrd::DiffusionDimension::kUser6:
        return ISMRMRD::DiffusionDimension::USER_6;
    case mrd::DiffusionDimension::kUser7:
        return ISMRMRD::DiffusionDimension::USER_7;
    default:
        throw std::runtime_error("Unknown DiffusionDimension: " + std::to_string((int)diffusionDimension));
    }
}

// Convert mrd::GradientDirectionType to ISMRMRD::GradientDirection
ISMRMRD::GradientDirection convert(mrd::GradientDirectionType &g)
{
    ISMRMRD::GradientDirection gradientDirection;
    gradientDirection.rl = g.rl;
    gradientDirection.ap = g.ap;
    gradientDirection.fh = g.fh;
    return gradientDirection;
}

// Convert mrd::DiffusionType to ISMRMRD::Diffusion
ISMRMRD::Diffusion convert(mrd::DiffusionType &d)
{
    ISMRMRD::Diffusion diffusion;
    diffusion.gradientDirection = convert(d.gradient_direction);
    diffusion.bvalue = d.bvalue;
    return diffusion;
}

// Convert mrd::SequenceParametersType to ISMRMRD::SequenceParameters
ISMRMRD::SequenceParameters convert(mrd::SequenceParametersType &s)
{
    ISMRMRD::SequenceParameters sequenceParameters;

    if (s.t_r.size())
    {
        sequenceParameters.TR = std::vector<float>(s.t_r.begin(), s.t_r.end());
    }

    if (s.t_e.size())
    {
        sequenceParameters.TE = std::vector<float>(s.t_e.begin(), s.t_e.end());
    }

    if (s.t_i.size())
    {
        sequenceParameters.TI = std::vector<float>(s.t_i.begin(), s.t_i.end());
    }

    if (s.flip_angle_deg.size())
    {
        sequenceParameters.flipAngle_deg = std::vector<float>(s.flip_angle_deg.begin(), s.flip_angle_deg.end());
    }

    if (s.sequence_type)
    {
        sequenceParameters.sequence_type = *s.sequence_type;
    }

    if (s.echo_spacing.size())
    {
        sequenceParameters.echo_spacing = std::vector<float>(s.echo_spacing.begin(), s.echo_spacing.end());
    }

    if (s.diffusion_dimension)
    {
        sequenceParameters.diffusionDimension = convert(*s.diffusion_dimension);
    }

    if (s.diffusion.size())
    {
        std::vector<ISMRMRD::Diffusion> diffusion;
        for (auto &d : s.diffusion)
        {
            diffusion.push_back(convert(d));
        }
        sequenceParameters.diffusion = diffusion;
    }

    if (s.diffusion_scheme)
    {
        sequenceParameters.diffusionScheme = *s.diffusion_scheme;
    }

    return sequenceParameters;
}

// Convert mrd::UserParameterBase64Type to ISMRMRD::UserParameterString
ISMRMRD::UserParameterString convert_userbase64(mrd::UserParameterBase64Type &u)
{
    ISMRMRD::UserParameterString userParameterString;
    userParameterString.name = u.name;
    userParameterString.value = u.value;
    return userParameterString;
}

// Convert mrd::UserParametersType to ISMRMRD::UserParameters
ISMRMRD::UserParameters convert(mrd::UserParametersType &u)
{
    ISMRMRD::UserParameters userParameters;

    for (auto &p : u.user_parameter_long)
    {
        userParameters.userParameterLong.push_back(convert(p));
    }

    for (auto &p : u.user_parameter_double)
    {
        userParameters.userParameterDouble.push_back(convert(p));
    }

    for (auto &p : u.user_parameter_string)
    {
        userParameters.userParameterString.push_back(convert(p));
    }

    for (auto &p : u.user_parameter_base_64)
    {
        userParameters.userParameterBase64.push_back(convert_userbase64(p));
    }

    return userParameters;
}

// Convert mrd::WaveformType to ISMRMRD::WaveformType
ISMRMRD::WaveformType convert(mrd::WaveformType &w)
{
    if (w == mrd::WaveformType::kEcg)
    {
        return ISMRMRD::WaveformType::ECG;
    }
    else if (w == mrd::WaveformType::kPulse)
    {
        return ISMRMRD::WaveformType::PULSE;
    }
    else if (w == mrd::WaveformType::kRespiratory)
    {
        return ISMRMRD::WaveformType::RESPIRATORY;
    }
    else if (w == mrd::WaveformType::kTrigger)
    {
        return ISMRMRD::WaveformType::TRIGGER;
    }
    else if (w == mrd::WaveformType::kGradientwaveform)
    {
        return ISMRMRD::WaveformType::GRADIENTWAVEFORM;
    }
    else if (w == mrd::WaveformType::kOther)
    {
        return ISMRMRD::WaveformType::OTHER;
    }
    else
    {
        throw std::runtime_error("Unknown WaveformType");
    }
}

// Convert mrd::WaveformInformationType to ISMRMRD::WaveformInformation
ISMRMRD::WaveformInformation convert(mrd::WaveformInformationType &w)
{
    ISMRMRD::WaveformInformation waveformInformation;
    waveformInformation.waveformName = w.waveform_name;
    waveformInformation.waveformType = convert(w.waveform_type);
    waveformInformation.userParameters = convert(w.user_parameters);
    return waveformInformation;
}

// Convert mrd::Header to ISMRMRD::IsmrmrdHeader
ISMRMRD::IsmrmrdHeader convert(mrd::Header &hdr)
{
    ISMRMRD::IsmrmrdHeader h;

    if (hdr.version)
    {
        h.version = *hdr.version;
    }

    if (hdr.subject_information)
    {
        h.subjectInformation = convert(*hdr.subject_information);
    }

    if (hdr.study_information)
    {
        h.studyInformation = convert(*hdr.study_information);
    }

    if (hdr.measurement_information)
    {
        h.measurementInformation = convert(*hdr.measurement_information);
    }

    if (hdr.acquisition_system_information)
    {
        h.acquisitionSystemInformation = convert(*hdr.acquisition_system_information);
    }

    h.experimentalConditions = convert(hdr.experimental_conditions);

    if (hdr.encoding.size() > 0)
    {
        for (auto e : hdr.encoding)
        {
            h.encoding.push_back(convert(e));
        }
    }
    else
    {
        throw std::runtime_error("No encoding found in mrd header");
    }

    if (hdr.sequence_parameters)
    {
        h.sequenceParameters = convert(*hdr.sequence_parameters);
    }

    if (hdr.user_parameters)
    {
        h.userParameters = convert(*hdr.user_parameters);
    }

    for (auto w : hdr.waveform_information)
    {
        h.waveformInformation.push_back(convert(w));
    }

    return h;
}

// Convert mrd::EncodingCounters to ISMRMRD::EncodingCounters
ISMRMRD::EncodingCounters convert(mrd::EncodingCounters &e)
{
    ISMRMRD::EncodingCounters encodingCounters;
    if (e.kspace_encode_step_1)
    {
        encodingCounters.kspace_encode_step_1 = *e.kspace_encode_step_1;
    }
    else
    {
        encodingCounters.kspace_encode_step_1 = 0;
    }

    if (e.kspace_encode_step_2)
    {
        encodingCounters.kspace_encode_step_2 = *e.kspace_encode_step_2;
    }
    else
    {
        encodingCounters.kspace_encode_step_2 = 0;
    }

    if (e.average)
    {
        encodingCounters.average = *e.average;
    }
    else
    {
        encodingCounters.average = 0;
    }

    if (e.slice)
    {
        encodingCounters.slice = *e.slice;
    }
    else
    {
        encodingCounters.slice = 0;
    }

    if (e.contrast)
    {
        encodingCounters.contrast = *e.contrast;
    }
    else
    {
        encodingCounters.contrast = 0;
    }

    if (e.phase)
    {
        encodingCounters.phase = *e.phase;
    }
    else
    {
        encodingCounters.phase = 0;
    }

    if (e.repetition)
    {
        encodingCounters.repetition = *e.repetition;
    }
    else
    {
        encodingCounters.repetition = 0;
    }

    if (e.set)
    {
        encodingCounters.set = *e.set;
    }
    else
    {
        encodingCounters.set = 0;
    }

    if (e.segment)
    {
        encodingCounters.segment = *e.segment;
    }
    else
    {
        encodingCounters.segment = 0;
    }

    if (e.user.size() > 8)
    {
        throw std::runtime_error("Too many user encoding counters");
    }

    for (size_t i = 0; i < e.user.size(); i++)
    {
        if (e.user[i] > 65535)
        {
            throw std::runtime_error("User encoding counter too large");
        }
        encodingCounters.user[i] = static_cast<uint16_t>(e.user[i]);
    }

    return encodingCounters;
}

// Convert mrd::Acquisition to ISMRMRD::Acquisition
ISMRMRD::Acquisition convert(mrd::Acquisition &acq)
{
    ISMRMRD::Acquisition acquisition;
    ISMRMRD::AcquisitionHeader hdr;

    hdr.version = ISMRMRD_VERSION_MAJOR;
    hdr.flags = acq.flags.Value();
    hdr.measurement_uid = acq.measurement_uid;
    hdr.scan_counter = acq.scan_counter ? *acq.scan_counter : 0;
    hdr.acquisition_time_stamp = acq.acquisition_time_stamp ? *acq.acquisition_time_stamp : 0;

    if (acq.physiology_time_stamp.size() > 3)
    {
        throw std::runtime_error("Too many physiology time stamps");
    }

    for (size_t i = 0; i < 3; i++)
    {
        hdr.physiology_time_stamp[i] = acq.physiology_time_stamp[i];
    }

    hdr.number_of_samples = acq.data.shape()[1];
    hdr.active_channels = acq.data.shape()[0];
    hdr.available_channels = acq.data.shape()[0];
    hdr.discard_pre = acq.discard_pre ? *acq.discard_pre : 0;
    hdr.discard_post = acq.discard_post ? *acq.discard_post : 0;
    hdr.encoding_space_ref = acq.encoding_space_ref ? *acq.encoding_space_ref : 0;
    hdr.center_sample = acq.center_sample ? *acq.center_sample : 0;
    hdr.trajectory_dimensions = acq.trajectory.shape()[0];
    hdr.sample_time_us = acq.sample_time_us ? *acq.sample_time_us : 0;
    hdr.position[0] = acq.position[0];
    hdr.position[1] = acq.position[1];
    hdr.position[2] = acq.position[2];
    hdr.read_dir[0] = acq.read_dir[0];
    hdr.read_dir[1] = acq.read_dir[1];
    hdr.read_dir[2] = acq.read_dir[2];
    hdr.phase_dir[0] = acq.phase_dir[0];
    hdr.phase_dir[1] = acq.phase_dir[1];
    hdr.phase_dir[2] = acq.phase_dir[2];
    hdr.slice_dir[0] = acq.slice_dir[0];
    hdr.slice_dir[1] = acq.slice_dir[1];
    hdr.slice_dir[2] = acq.slice_dir[2];
    hdr.patient_table_position[0] = acq.patient_table_position[0];
    hdr.patient_table_position[1] = acq.patient_table_position[1];
    hdr.patient_table_position[2] = acq.patient_table_position[2];
    hdr.idx.kspace_encode_step_1 = acq.idx.kspace_encode_step_1 ? *acq.idx.kspace_encode_step_1 : 0;
    hdr.idx.kspace_encode_step_2 = acq.idx.kspace_encode_step_2 ? *acq.idx.kspace_encode_step_2 : 0;
    hdr.idx.average = acq.idx.average ? *acq.idx.average : 0;
    hdr.idx.slice = acq.idx.slice ? *acq.idx.slice : 0;
    hdr.idx.contrast = acq.idx.contrast ? *acq.idx.contrast : 0;
    hdr.idx.phase = acq.idx.phase ? *acq.idx.phase : 0;
    hdr.idx.repetition = acq.idx.repetition ? *acq.idx.repetition : 0;
    hdr.idx.set = acq.idx.set ? *acq.idx.set : 0;
    hdr.idx.segment = acq.idx.segment ? *acq.idx.segment : 0;

    if (acq.idx.user.size() > 8)
    {
        throw std::runtime_error("Too many user parameters");
    }

    for (size_t i = 0; i < acq.idx.user.size(); i++)
    {
        hdr.idx.user[i] = acq.idx.user[i];
    }

    if (acq.user_int.size() > ISMRMRD::ISMRMRD_USER_INTS)
    {
        throw std::runtime_error("Too many user parameters");
    }

    for (size_t i = 0; i < acq.user_int.size(); i++)
    {
        hdr.user_int[i] = acq.user_int[i];
    }

    if (acq.user_float.size() > ISMRMRD::ISMRMRD_USER_FLOATS)
    {
        throw std::runtime_error("Too many user parameters");
    }

    for (size_t i = 0; i < acq.user_float.size(); i++)
    {
        hdr.user_float[i] = acq.user_float[i];
    }

    acquisition.setHead(hdr);

    mrd::AcquisitionData data = acq.data;
    for (uint16_t c = 0; c < hdr.active_channels; c++)
    {
        for (uint16_t s = 0; s < hdr.number_of_samples; s++)
        {
            acquisition.data(s, c) = data(c, s);
        }
    }

    mrd::TrajectoryData traj = acq.trajectory;
    for (uint16_t d = 0; d < hdr.trajectory_dimensions; d++)
    {
        for (uint16_t s = 0; s < hdr.number_of_samples; s++)
        {
            acquisition.traj(s, d) = traj(d, s);
        }
    }

    return acquisition;
}

// Convert mrd::Waveform<uint32_t> to ISMRMRD::Waveform
ISMRMRD::Waveform convert(mrd::Waveform<uint32_t> &wfm)
{
    ISMRMRD::Waveform waveform(wfm.Channels(), wfm.NumberOfSamples());
    waveform.head.flags = wfm.flags;
    waveform.head.measurement_uid = wfm.measurement_uid;
    waveform.head.scan_counter = wfm.scan_counter;
    waveform.head.time_stamp = wfm.time_stamp;
    waveform.head.sample_time_us = wfm.sample_time_us;

    waveform.head.channels = wfm.data.shape()[0];
    waveform.head.number_of_samples = wfm.data.shape()[1];

    for (uint16_t c = 0; c < waveform.head.channels; c++)
    {
        for (uint16_t s = 0; s < waveform.head.number_of_samples; s++)
        {
            waveform.data[c * waveform.head.number_of_samples + s] = wfm.data(c, s);
        }
    }

    return waveform;
}

// Convert mrd::Image<T> to ISMRMRD::Image<T>
template <class T>
ISMRMRD::Image<T> convert(mrd::Image<T> &image)
{
    ISMRMRD::Image<T> im(image.Cols(), image.Rows(), image.Slices(), image.Channels());
    im.setFlags(image.flags.Value());
    im.setMeasurementUid(image.measurement_uid);
    im.setFieldOfView(image.field_of_view[0], image.field_of_view[1], image.field_of_view[2]);
    im.setPosition(image.position[0], image.position[1], image.position[2]);
    im.setReadDirection(image.col_dir[0], image.col_dir[1], image.col_dir[2]);
    im.setPhaseDirection(image.line_dir[0], image.line_dir[1], image.line_dir[2]);
    im.setSliceDirection(image.slice_dir[0], image.slice_dir[1], image.slice_dir[2]);
    im.setPatientTablePosition(image.patient_table_position[0], image.patient_table_position[1], image.patient_table_position[2]);
    im.setAverage(image.average ? *image.average : 0);
    im.setSlice(image.slice ? *image.slice : 0);
    im.setContrast(image.contrast ? *image.contrast : 0);
    im.setPhase(image.phase ? *image.phase : 0);
    im.setRepetition(image.repetition ? *image.repetition : 0);
    im.setSet(image.set ? *image.set : 0);
    im.setAcquisitionTimeStamp(image.acquisition_time_stamp ? *image.acquisition_time_stamp : 0);
    im.setPhysiologyTimeStamp(0, image.physiology_time_stamp[0]);
    im.setPhysiologyTimeStamp(1, image.physiology_time_stamp[1]);
    im.setPhysiologyTimeStamp(2, image.physiology_time_stamp[2]);
    switch (image.image_type)
    {
    case mrd::ImageType::kMagnitude:
        im.setImageType(ISMRMRD::ISMRMRD_IMTYPE_MAGNITUDE);
        break;
    case mrd::ImageType::kPhase:
        im.setImageType(ISMRMRD::ISMRMRD_IMTYPE_PHASE);
        break;
    case mrd::ImageType::kReal:
        im.setImageType(ISMRMRD::ISMRMRD_IMTYPE_REAL);
        break;
    case mrd::ImageType::kImag:
        im.setImageType(ISMRMRD::ISMRMRD_IMTYPE_IMAG);
        break;
    case mrd::ImageType::kComplex:
        im.setImageType(ISMRMRD::ISMRMRD_IMTYPE_COMPLEX);
        break;
    default:
        throw std::runtime_error("Unknown image type");
    }
    im.setImageIndex(image.image_index ? *image.image_index : 0);
    im.setImageSeriesIndex(image.image_series_index ? *image.image_series_index : 0);

    if (image.user_int.size() > ISMRMRD::ISMRMRD_USER_INTS)
    {
        throw std::runtime_error("Too many user_int values");
    }

    for (size_t i = 0; i < image.user_int.size(); i++)
    {
        im.setUserInt(i, image.user_int[i]);
    }

    if (image.user_float.size() > ISMRMRD::ISMRMRD_USER_FLOATS)
    {
        throw std::runtime_error("Too many user_float values");
    }

    for (size_t i = 0; i < image.user_float.size(); i++)
    {
        im.setUserFloat(i, image.user_float[i]);
    }

    ISMRMRD::MetaContainer meta;
    for (auto it = image.meta.begin(); it != image.meta.end(); it++)
    {
        for (auto it2 = it->second.begin(); it2 != it->second.end(); it2++)
        {
            meta.append(it->first.c_str(), (*it2).c_str());
        }
    }

    std::stringstream ss;
    ISMRMRD::serialize(meta, ss);
    im.setAttributeString(ss.str());

    for (int c = 0; c < im.getNumberOfChannels(); c++)
    {
        for (int z = 0; z < im.getMatrixSizeZ(); z++)
        {
            for (int y = 0; y < im.getMatrixSizeY(); y++)
            {
                for (int x = 0; x < im.getMatrixSizeX(); x++)
                {
                    im(x, y, z, c) = image.data(c, z, y, x);
                }
            }
        }
    }

    return im;
}

int main()
{
    ISMRMRD::OStreamView ws(std::cout);
    ISMRMRD::ProtocolSerializer serializer(ws);
    mrd::binary::MrdReader r(std::cin);

    std::optional<mrd::Header> header;
    r.ReadHeader(header);
    if (header)
    {
        serializer.serialize(convert(*header));
    }

    mrd::StreamItem item;
    while (r.ReadData(item))
    {
        std::visit([&serializer](auto &&arg)
                   { serializer.serialize(convert(arg)); },
                   item);
    }

    serializer.close();

    return 0;
}

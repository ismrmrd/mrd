#include "converters.h"

#include <ismrmrd/meta.h>
#include <ismrmrd/version.h>

#include <date/date.h>
#include <xtensor/views/xview.hpp>

namespace mrd::converters {

std::string date_to_string(const yardl::Date& d) {
  std::stringstream ss;
  date::local_days ld(d.time_since_epoch());
  ss << date::format("%F", ld);
  return ss.str();
}

std::string time_to_string(const yardl::Time& t) {
  std::stringstream ss;
  ss << date::format("%T", t);
  return ss.str();
}

// Convert mrd::SubjectInformationType to ISMRMRD::SubjectInformation
ISMRMRD::SubjectInformation convert(mrd::SubjectInformationType& subjectInformation) {
  ISMRMRD::SubjectInformation s;
  if (subjectInformation.patient_name) {
    s.patientName = *subjectInformation.patient_name;
  }

  if (subjectInformation.patient_weight_kg) {
    s.patientWeight_kg = *subjectInformation.patient_weight_kg;
  }

  if (subjectInformation.patient_height_m) {
    s.patientHeight_m = *subjectInformation.patient_height_m;
  }

  if (subjectInformation.patient_id) {
    s.patientID = *subjectInformation.patient_id;
  }

  if (subjectInformation.patient_birthdate) {
    s.patientBirthdate = date_to_string(*subjectInformation.patient_birthdate);
  }

  if (subjectInformation.patient_gender) {
    if (*subjectInformation.patient_gender == mrd::PatientGender::kF) {
      s.patientGender = "F";
    } else if (*subjectInformation.patient_gender == mrd::PatientGender::kM) {
      s.patientGender = "M";
    } else if (*subjectInformation.patient_gender == mrd::PatientGender::kO) {
      s.patientGender = "O";
    } else {
      throw std::runtime_error("Unknown gender");
    }
  }

  return s;
}

// Convert mrd::StudyInformationType to ISMRMRD::StudyInformation
ISMRMRD::StudyInformation convert(mrd::StudyInformationType& studyInformation) {
  ISMRMRD::StudyInformation s;

  if (studyInformation.study_date) {
    s.studyDate = date_to_string(*studyInformation.study_date);
  }

  if (studyInformation.study_time) {
    s.studyTime = time_to_string(*studyInformation.study_time);
  }

  if (studyInformation.study_id) {
    s.studyID = *studyInformation.study_id;
  }

  if (studyInformation.accession_number) {
    s.accessionNumber = *studyInformation.accession_number;
  }

  if (studyInformation.referring_physician_name) {
    s.referringPhysicianName = *studyInformation.referring_physician_name;
  }

  if (studyInformation.study_description) {
    s.studyDescription = *studyInformation.study_description;
  }

  if (studyInformation.study_instance_uid) {
    s.studyInstanceUID = *studyInformation.study_instance_uid;
  }

  if (studyInformation.body_part_examined) {
    s.bodyPartExamined = *studyInformation.body_part_examined;
  }

  return s;
}

// Convert mrd::PatientPosition to ISMRMRD patient position string
std::string patient_position_to_string(mrd::PatientPosition& p) {
  if (p == mrd::PatientPosition::kHFP) {
    return "HFP";
  } else if (p == mrd::PatientPosition::kHFS) {
    return "HFS";
  } else if (p == mrd::PatientPosition::kHFDR) {
    return "HFDR";
  } else if (p == mrd::PatientPosition::kHFDL) {
    return "HFDL";
  } else if (p == mrd::PatientPosition::kFFP) {
    return "FFP";
  } else if (p == mrd::PatientPosition::kFFS) {
    return "FFS";
  } else if (p == mrd::PatientPosition::kFFDR) {
    return "FFDR";
  } else if (p == mrd::PatientPosition::kFFDL) {
    return "FFDL";
  } else {
    throw std::runtime_error("Unknown Patient Position");
  }
}

// Convert mrd::ThreeDimensionalFloat to ISMRMRD::threeDimensionalFloat
ISMRMRD::threeDimensionalFloat convert(mrd::ThreeDimensionalFloat& threeDimensionalFloat) {
  ISMRMRD::threeDimensionalFloat t;
  t.x = threeDimensionalFloat.x;
  t.y = threeDimensionalFloat.y;
  t.z = threeDimensionalFloat.z;
  return t;
}

// Convert mrd::MeasurementDependencyType to ISMRMRD::MeasurementDependency
ISMRMRD::MeasurementDependency convert(mrd::MeasurementDependencyType& measurementDependency) {
  ISMRMRD::MeasurementDependency m;
  m.measurementID = measurementDependency.measurement_id;
  m.dependencyType = measurementDependency.dependency_type;
  return m;
}

// Convert mrd::MeasurementInformationType to ISMRMRD::MeasurementInformation
ISMRMRD::MeasurementInformation convert(mrd::MeasurementInformationType& measurementInformation) {
  ISMRMRD::MeasurementInformation m;

  if (measurementInformation.measurement_id) {
    m.measurementID = *measurementInformation.measurement_id;
  }

  if (measurementInformation.series_date) {
    m.seriesDate = date_to_string(*measurementInformation.series_date);
  }

  if (measurementInformation.series_time) {
    m.seriesTime = time_to_string(*measurementInformation.series_time);
  }

  m.patientPosition = patient_position_to_string(measurementInformation.patient_position);

  if (measurementInformation.relative_table_position) {
    m.relativeTablePosition = convert(*measurementInformation.relative_table_position);
  }

  if (measurementInformation.initial_series_number) {
    m.initialSeriesNumber = *measurementInformation.initial_series_number;
  }

  if (measurementInformation.protocol_name) {
    m.protocolName = *measurementInformation.protocol_name;
  }

  if (measurementInformation.sequence_name) {
    m.sequenceName = *measurementInformation.sequence_name;
  }

  if (measurementInformation.series_description) {
    m.seriesDescription = *measurementInformation.series_description;
  }

  for (auto& dependency : measurementInformation.measurement_dependency) {
    m.measurementDependency.push_back(convert(dependency));
  }

  if (measurementInformation.series_instance_uid_root) {
    m.seriesInstanceUIDRoot = *measurementInformation.series_instance_uid_root;
  }

  if (measurementInformation.frame_of_reference_uid) {
    m.frameOfReferenceUID = *measurementInformation.frame_of_reference_uid;
  }

  if (measurementInformation.referenced_image_sequence) {
    for (auto& image : measurementInformation.referenced_image_sequence->referenced_sop_instance_uid) {
      ISMRMRD::ReferencedImageSequence referencedImage;
      referencedImage.referencedSOPInstanceUID = image;
      m.referencedImageSequence.push_back(referencedImage);
    }
  }

  return m;
}

// Convert mrd::AcquisitionSystemInformationType to ISMRMRD::AcquisitionSystemInformation
ISMRMRD::AcquisitionSystemInformation convert(mrd::AcquisitionSystemInformationType& a) {
  ISMRMRD::AcquisitionSystemInformation asi;

  if (a.system_vendor) {
    asi.systemVendor = *a.system_vendor;
  }

  if (a.system_model) {
    asi.systemModel = *a.system_model;
  }

  if (a.system_field_strength_t) {
    asi.systemFieldStrength_T = *a.system_field_strength_t;
  }

  if (a.relative_receiver_noise_bandwidth) {
    asi.relativeReceiverNoiseBandwidth = *a.relative_receiver_noise_bandwidth;
  }

  if (a.receiver_channels) {
    asi.receiverChannels = *a.receiver_channels;
  }

  if (a.coil_label.size() > 0) {
    for (auto& c : a.coil_label) {
      ISMRMRD::CoilLabel cl;
      cl.coilName = c.coil_name;
      cl.coilNumber = c.coil_number;
      asi.coilLabel.push_back(cl);
    }
  }

  if (a.institution_name) {
    asi.institutionName = *a.institution_name;
  }

  if (a.station_name) {
    asi.stationName = *a.station_name;
  }

  if (a.device_id) {
    asi.deviceID = *a.device_id;
  }

  if (a.device_serial_number) {
    asi.deviceSerialNumber = *a.device_serial_number;
  }

  return asi;
}

// Convert mrd::ExperimentalConditionsType to ISMRMRD::ExperimentalConditions
ISMRMRD::ExperimentalConditions convert(mrd::ExperimentalConditionsType& e) {
  ISMRMRD::ExperimentalConditions ec;
  ec.H1resonanceFrequency_Hz = e.h1resonance_frequency_hz;
  return ec;
}

// Convert mrd::MatrixSizeType to ISMRMRD::MatrixSize
ISMRMRD::MatrixSize convert(mrd::MatrixSizeType& m) {
  ISMRMRD::MatrixSize matrixSize;
  matrixSize.x = m.x;
  matrixSize.y = m.y;
  matrixSize.z = m.z;
  return matrixSize;
}

// Convert mrd::FieldOfViewmm to ISMRMRD::FieldOfView_mm
ISMRMRD::FieldOfView_mm convert(mrd::FieldOfViewMm& f) {
  ISMRMRD::FieldOfView_mm fieldOfView;
  fieldOfView.x = f.x;
  fieldOfView.y = f.y;
  fieldOfView.z = f.z;
  return fieldOfView;
}

// Convert mrd::EncodingSpaceType to ISMRMRD::EncodingSpace
ISMRMRD::EncodingSpace convert(mrd::EncodingSpaceType& e) {
  ISMRMRD::EncodingSpace encodingSpace;
  encodingSpace.matrixSize = convert(e.matrix_size);
  encodingSpace.fieldOfView_mm = convert(e.field_of_view_mm);
  return encodingSpace;
}

// Convert mrd::LimitType to ISMRMRD::Limit
ISMRMRD::Limit convert(mrd::LimitType& l) {
  ISMRMRD::Limit limit;
  limit.minimum = l.minimum;
  limit.maximum = l.maximum;
  limit.center = l.center;
  return limit;
}

// Convert mrd::EncodingLimitsType to ISMRMRD::EncodingLimits
ISMRMRD::EncodingLimits convert(mrd::EncodingLimitsType& encodingLimit) {
  ISMRMRD::EncodingLimits el;

  if (encodingLimit.kspace_encoding_step_0) {
    el.kspace_encoding_step_0 = convert(*encodingLimit.kspace_encoding_step_0);
  }

  if (encodingLimit.kspace_encoding_step_1) {
    el.kspace_encoding_step_1 = convert(*encodingLimit.kspace_encoding_step_1);
  }

  if (encodingLimit.kspace_encoding_step_2) {
    el.kspace_encoding_step_2 = convert(*encodingLimit.kspace_encoding_step_2);
  }

  if (encodingLimit.average) {
    el.average = convert(*encodingLimit.average);
  }

  if (encodingLimit.slice) {
    el.slice = convert(*encodingLimit.slice);
  }

  if (encodingLimit.contrast) {
    el.contrast = convert(*encodingLimit.contrast);
  }

  if (encodingLimit.phase) {
    el.phase = convert(*encodingLimit.phase);
  }

  if (encodingLimit.repetition) {
    el.repetition = convert(*encodingLimit.repetition);
  }

  if (encodingLimit.set) {
    el.set = convert(*encodingLimit.set);
  }

  if (encodingLimit.segment) {
    el.segment = convert(*encodingLimit.segment);
  }

  if (encodingLimit.user_0) {
    el.user[0] = convert(*encodingLimit.user_0);
  }

  if (encodingLimit.user_1) {
    el.user[1] = convert(*encodingLimit.user_1);
  }

  if (encodingLimit.user_2) {
    el.user[2] = convert(*encodingLimit.user_2);
  }

  if (encodingLimit.user_3) {
    el.user[3] = convert(*encodingLimit.user_3);
  }

  if (encodingLimit.user_4) {
    el.user[4] = convert(*encodingLimit.user_4);
  }

  if (encodingLimit.user_5) {
    el.user[5] = convert(*encodingLimit.user_5);
  }

  if (encodingLimit.user_6) {
    el.user[6] = convert(*encodingLimit.user_6);
  }

  if (encodingLimit.user_7) {
    el.user[7] = convert(*encodingLimit.user_7);
  }

  return el;
}

// Convert mrd::UserParameterLongType to ISMRMRD::UserParameterLong
ISMRMRD::UserParameterLong convert(mrd::UserParameterLongType& u) {
  ISMRMRD::UserParameterLong userParameterLong;
  userParameterLong.name = u.name;
  userParameterLong.value = u.value;
  return userParameterLong;
}

// Convert mrd::UserParameterDoubleType to ISMRMRD::UserParameterDouble
ISMRMRD::UserParameterDouble convert(mrd::UserParameterDoubleType& u) {
  ISMRMRD::UserParameterDouble userParameterDouble;
  userParameterDouble.name = u.name;
  userParameterDouble.value = u.value;
  return userParameterDouble;
}

// Convert mrd::UserParameterStringType to ISMRMRD::UserParameterString
ISMRMRD::UserParameterString convert(mrd::UserParameterStringType& u) {
  ISMRMRD::UserParameterString userParameterString;
  userParameterString.name = u.name;
  userParameterString.value = u.value;
  return userParameterString;
}

// Convert mrd::TrajectoryDescriptionType to ISMRMRD::TrajectoryDescription
ISMRMRD::TrajectoryDescription convert(mrd::TrajectoryDescriptionType& t) {
  ISMRMRD::TrajectoryDescription trajectoryDescription;
  trajectoryDescription.identifier = t.identifier;

  for (auto& u : t.user_parameter_long) {
    trajectoryDescription.userParameterLong.push_back(convert(u));
  }

  for (auto& u : t.user_parameter_double) {
    trajectoryDescription.userParameterDouble.push_back(convert(u));
  }

  for (auto& u : t.user_parameter_string) {
    trajectoryDescription.userParameterString.push_back(convert(u));
  }

  if (t.comment) {
    trajectoryDescription.comment = *t.comment;
  }

  return trajectoryDescription;
}

// Convert mrd::AccelerationFactorType to ISMRMRD::AccelerationFactor
ISMRMRD::AccelerationFactor convert(mrd::AccelerationFactorType& a) {
  ISMRMRD::AccelerationFactor accelerationFactor;
  accelerationFactor.kspace_encoding_step_1 = a.kspace_encoding_step_1;
  accelerationFactor.kspace_encoding_step_2 = a.kspace_encoding_step_2;
  return accelerationFactor;
}

// Convert mrd::CalibrationMode to ISMRMRD calibration mode string
std::string calibration_mode_to_string(mrd::CalibrationMode& m) {
  switch (m) {
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
std::string interleaving_dimension_to_string(mrd::InterleavingDimension& d) {
  switch (d) {
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
ISMRMRD::MultibandSpacing convert(mrd::MultibandSpacingType& m) {
  ISMRMRD::MultibandSpacing multibandSpacing;
  for (auto s : m.d_z) {
    multibandSpacing.dZ.push_back(s);
  }
  return multibandSpacing;
}

// Convert mrd::Calibration to ISMRMRD::MultibandCalibrationType
ISMRMRD::MultibandCalibrationType convert(mrd::Calibration& m) {
  switch (m) {
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
ISMRMRD::Multiband convert(mrd::MultibandType& m) {
  ISMRMRD::Multiband multiband;
  for (auto s : m.spacing) {
    multiband.spacing.push_back(convert(s));
  }
  multiband.deltaKz = m.delta_kz;
  multiband.multiband_factor = m.multiband_factor;
  multiband.calibration = convert(m.calibration);
  multiband.calibration_encoding = m.calibration_encoding;
  return multiband;
}

// Convert mrd::ParallelImagingType to ISMRMRD::ParallelImaging
ISMRMRD::ParallelImaging convert(mrd::ParallelImagingType& p) {
  ISMRMRD::ParallelImaging parallelImaging;
  parallelImaging.accelerationFactor = convert(p.acceleration_factor);
  if (p.calibration_mode) {
    parallelImaging.calibrationMode = calibration_mode_to_string(*p.calibration_mode);
  }
  if (p.interleaving_dimension) {
    parallelImaging.interleavingDimension = interleaving_dimension_to_string(*p.interleaving_dimension);
  }
  if (p.multiband) {
    parallelImaging.multiband = convert(*p.multiband);
  }
  return parallelImaging;
}

// Convert mrd::EncodingType to ISMRMRD::Encoding
ISMRMRD::Encoding convert(mrd::EncodingType& e) {
  ISMRMRD::Encoding encoding;

  encoding.encodedSpace = convert(e.encoded_space);
  encoding.reconSpace = convert(e.recon_space);
  encoding.encodingLimits = convert(e.encoding_limits);

  switch (e.trajectory) {
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

  if (e.trajectory_description) {
    encoding.trajectoryDescription = convert(*e.trajectory_description);
  }

  if (e.parallel_imaging) {
    encoding.parallelImaging = convert(*e.parallel_imaging);
  }

  if (e.echo_train_length) {
    encoding.echoTrainLength = *e.echo_train_length;
  }

  return encoding;
}

// Convert mrd::DiffusionDimension to ISMRMRD::DiffusionDimension
ISMRMRD::DiffusionDimension convert(mrd::DiffusionDimension& diffusionDimension) {
  switch (diffusionDimension) {
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
ISMRMRD::GradientDirection convert(mrd::GradientDirectionType& g) {
  ISMRMRD::GradientDirection gradientDirection;
  gradientDirection.rl = g.rl;
  gradientDirection.ap = g.ap;
  gradientDirection.fh = g.fh;
  return gradientDirection;
}

// Convert mrd::DiffusionType to ISMRMRD::Diffusion
ISMRMRD::Diffusion convert(mrd::DiffusionType& d) {
  ISMRMRD::Diffusion diffusion;
  diffusion.gradientDirection = convert(d.gradient_direction);
  diffusion.bvalue = d.bvalue;
  return diffusion;
}

// Convert mrd::SequenceParametersType to ISMRMRD::SequenceParameters
ISMRMRD::SequenceParameters convert(mrd::SequenceParametersType& s) {
  ISMRMRD::SequenceParameters sequenceParameters;

  if (s.t_r.size()) {
    sequenceParameters.TR = std::vector<float>(s.t_r.begin(), s.t_r.end());
  }

  if (s.t_e.size()) {
    sequenceParameters.TE = std::vector<float>(s.t_e.begin(), s.t_e.end());
  }

  if (s.t_i.size()) {
    sequenceParameters.TI = std::vector<float>(s.t_i.begin(), s.t_i.end());
  }

  if (s.flip_angle_deg.size()) {
    sequenceParameters.flipAngle_deg = std::vector<float>(s.flip_angle_deg.begin(), s.flip_angle_deg.end());
  }

  if (s.sequence_type) {
    sequenceParameters.sequence_type = *s.sequence_type;
  }

  if (s.echo_spacing.size()) {
    sequenceParameters.echo_spacing = std::vector<float>(s.echo_spacing.begin(), s.echo_spacing.end());
  }

  if (s.diffusion_dimension) {
    sequenceParameters.diffusionDimension = convert(*s.diffusion_dimension);
  }

  if (s.diffusion.size()) {
    std::vector<ISMRMRD::Diffusion> diffusion;
    for (auto& d : s.diffusion) {
      diffusion.push_back(convert(d));
    }
    sequenceParameters.diffusion = diffusion;
  }

  if (s.diffusion_scheme) {
    sequenceParameters.diffusionScheme = *s.diffusion_scheme;
  }

  return sequenceParameters;
}

// Convert mrd::UserParameterBase64Type to ISMRMRD::UserParameterString
ISMRMRD::UserParameterString convert_userbase64(mrd::UserParameterBase64Type& u) {
  ISMRMRD::UserParameterString userParameterString;
  userParameterString.name = u.name;
  userParameterString.value = u.value;
  return userParameterString;
}

// Convert mrd::UserParametersType to ISMRMRD::UserParameters
ISMRMRD::UserParameters convert(mrd::UserParametersType& u) {
  ISMRMRD::UserParameters userParameters;

  for (auto& p : u.user_parameter_long) {
    userParameters.userParameterLong.push_back(convert(p));
  }

  for (auto& p : u.user_parameter_double) {
    userParameters.userParameterDouble.push_back(convert(p));
  }

  for (auto& p : u.user_parameter_string) {
    userParameters.userParameterString.push_back(convert(p));
  }

  for (auto& p : u.user_parameter_base64) {
    userParameters.userParameterBase64.push_back(convert_userbase64(p));
  }

  return userParameters;
}

// Convert mrd::WaveformType to ISMRMRD::WaveformType
ISMRMRD::WaveformType convert(mrd::WaveformType& w) {
  if (w == mrd::WaveformType::kEcg) {
    return ISMRMRD::WaveformType::ECG;
  } else if (w == mrd::WaveformType::kPulse) {
    return ISMRMRD::WaveformType::PULSE;
  } else if (w == mrd::WaveformType::kRespiratory) {
    return ISMRMRD::WaveformType::RESPIRATORY;
  } else if (w == mrd::WaveformType::kTrigger) {
    return ISMRMRD::WaveformType::TRIGGER;
  } else if (w == mrd::WaveformType::kGradientwaveform) {
    return ISMRMRD::WaveformType::GRADIENTWAVEFORM;
  } else if (w == mrd::WaveformType::kOther) {
    return ISMRMRD::WaveformType::OTHER;
  } else {
    throw std::runtime_error("Unknown WaveformType");
  }
}

// Convert mrd::WaveformInformationType to ISMRMRD::WaveformInformation
ISMRMRD::WaveformInformation convert(mrd::WaveformInformationType& w) {
  ISMRMRD::WaveformInformation waveformInformation;
  waveformInformation.waveformName = w.waveform_name;
  waveformInformation.waveformType = convert(w.waveform_type);
  waveformInformation.userParameters = convert(w.user_parameters);
  return waveformInformation;
}

// Convert mrd::Header to ISMRMRD::IsmrmrdHeader
ISMRMRD::IsmrmrdHeader convert(mrd::Header& hdr) {
  ISMRMRD::IsmrmrdHeader h;

  if (hdr.version) {
    h.version = *hdr.version;
  }

  if (hdr.subject_information) {
    h.subjectInformation = convert(*hdr.subject_information);
  }

  if (hdr.study_information) {
    h.studyInformation = convert(*hdr.study_information);
  }

  if (hdr.measurement_information) {
    h.measurementInformation = convert(*hdr.measurement_information);
  }

  if (hdr.acquisition_system_information) {
    h.acquisitionSystemInformation = convert(*hdr.acquisition_system_information);
  }

  h.experimentalConditions = convert(hdr.experimental_conditions);

  if (hdr.encoding.size() > 0) {
    for (auto e : hdr.encoding) {
      h.encoding.push_back(convert(e));
    }
  } else {
    throw std::runtime_error("No encoding found in mrd header");
  }

  if (hdr.sequence_parameters) {
    h.sequenceParameters = convert(*hdr.sequence_parameters);
  }

  if (hdr.user_parameters) {
    h.userParameters = convert(*hdr.user_parameters);
  }

  for (auto w : hdr.waveform_information) {
    h.waveformInformation.push_back(convert(w));
  }

  return h;
}

// Convert mrd::EncodingCounters to ISMRMRD::EncodingCounters
ISMRMRD::EncodingCounters convert(mrd::EncodingCounters& e) {
  ISMRMRD::EncodingCounters encodingCounters;
  if (e.kspace_encode_step_1) {
    encodingCounters.kspace_encode_step_1 = *e.kspace_encode_step_1;
  } else {
    encodingCounters.kspace_encode_step_1 = 0;
  }

  if (e.kspace_encode_step_2) {
    encodingCounters.kspace_encode_step_2 = *e.kspace_encode_step_2;
  } else {
    encodingCounters.kspace_encode_step_2 = 0;
  }

  if (e.average) {
    encodingCounters.average = *e.average;
  } else {
    encodingCounters.average = 0;
  }

  if (e.slice) {
    encodingCounters.slice = *e.slice;
  } else {
    encodingCounters.slice = 0;
  }

  if (e.contrast) {
    encodingCounters.contrast = *e.contrast;
  } else {
    encodingCounters.contrast = 0;
  }

  if (e.phase) {
    encodingCounters.phase = *e.phase;
  } else {
    encodingCounters.phase = 0;
  }

  if (e.repetition) {
    encodingCounters.repetition = *e.repetition;
  } else {
    encodingCounters.repetition = 0;
  }

  if (e.set) {
    encodingCounters.set = *e.set;
  } else {
    encodingCounters.set = 0;
  }

  if (e.segment) {
    encodingCounters.segment = *e.segment;
  } else {
    encodingCounters.segment = 0;
  }

  if (e.user.size() > 8) {
    throw std::runtime_error("Too many user encoding counters");
  }

  for (size_t i = 0; i < e.user.size(); i++) {
    if (e.user[i] > 65535) {
      throw std::runtime_error("User encoding counter too large");
    }
    encodingCounters.user[i] = static_cast<uint16_t>(e.user[i]);
  }

  return encodingCounters;
}

// Convert mrd::Acquisition to ISMRMRD::Acquisition
ISMRMRD::Acquisition convert(mrd::Acquisition& acq) {
  ISMRMRD::Acquisition acquisition;
  ISMRMRD::AcquisitionHeader hdr;
  mrd::AcquisitionHeader& head = acq.head;

  hdr.version = ISMRMRD_VERSION_MAJOR;
  hdr.flags = head.flags.Value();
  hdr.measurement_uid = head.measurement_uid;
  hdr.scan_counter = head.scan_counter.value_or(0);
  hdr.acquisition_time_stamp = head.acquisition_time_stamp_ns.value_or(0) / 1e6; // ns to ms

  if (head.physiology_time_stamp_ns.size() > 3) {
    throw std::runtime_error("Too many physiology time stamps");
  }

  for (size_t i = 0; i < ISMRMRD::ISMRMRD_PHYS_STAMPS; i++) {
    if (head.physiology_time_stamp_ns.size() > i) {
      hdr.physiology_time_stamp[i] = head.physiology_time_stamp_ns[i] / 1e6; // ns to ms
    }
  }

  hdr.number_of_samples = acq.Samples();
  hdr.active_channels = acq.Coils();
  hdr.available_channels = acq.Coils();
  hdr.discard_pre = head.discard_pre.value_or(0);
  hdr.discard_post = head.discard_post.value_or(0);
  hdr.encoding_space_ref = head.encoding_space_ref.value_or(0);
  hdr.center_sample = head.center_sample.value_or(0);
  hdr.trajectory_dimensions = acq.trajectory.shape()[0];
  hdr.sample_time_us = static_cast<float>(head.sample_time_ns.value_or(0) / 1e3); // ns to us as float
  hdr.position[0] = head.position[0];
  hdr.position[1] = head.position[1];
  hdr.position[2] = head.position[2];
  hdr.read_dir[0] = head.read_dir[0];
  hdr.read_dir[1] = head.read_dir[1];
  hdr.read_dir[2] = head.read_dir[2];
  hdr.phase_dir[0] = head.phase_dir[0];
  hdr.phase_dir[1] = head.phase_dir[1];
  hdr.phase_dir[2] = head.phase_dir[2];
  hdr.slice_dir[0] = head.slice_dir[0];
  hdr.slice_dir[1] = head.slice_dir[1];
  hdr.slice_dir[2] = head.slice_dir[2];
  hdr.patient_table_position[0] = head.patient_table_position[0];
  hdr.patient_table_position[1] = head.patient_table_position[1];
  hdr.patient_table_position[2] = head.patient_table_position[2];
  hdr.idx.kspace_encode_step_1 = head.idx.kspace_encode_step_1.value_or(0);
  hdr.idx.kspace_encode_step_2 = head.idx.kspace_encode_step_2.value_or(0);
  hdr.idx.average = head.idx.average.value_or(0);
  hdr.idx.slice = head.idx.slice.value_or(0);
  hdr.idx.contrast = head.idx.contrast.value_or(0);
  hdr.idx.phase = head.idx.phase.value_or(0);
  hdr.idx.repetition = head.idx.repetition.value_or(0);
  hdr.idx.set = head.idx.set.value_or(0);
  hdr.idx.segment = head.idx.segment.value_or(0);

  if (head.idx.user.size() > 8) {
    throw std::runtime_error("Too many user parameters");
  }

  for (size_t i = 0; i < head.idx.user.size(); i++) {
    hdr.idx.user[i] = head.idx.user[i];
  }

  if (head.user_int.size() > ISMRMRD::ISMRMRD_USER_INTS) {
    throw std::runtime_error("Too many user parameters");
  }

  for (size_t i = 0; i < head.user_int.size(); i++) {
    hdr.user_int[i] = head.user_int[i];
  }

  if (head.user_float.size() > ISMRMRD::ISMRMRD_USER_FLOATS) {
    throw std::runtime_error("Too many user parameters");
  }

  for (size_t i = 0; i < head.user_float.size(); i++) {
    hdr.user_float[i] = head.user_float[i];
  }

  acquisition.setHead(hdr);

  mrd::AcquisitionData data = acq.data;
  for (uint16_t c = 0; c < hdr.active_channels; c++) {
    for (uint16_t s = 0; s < hdr.number_of_samples; s++) {
      acquisition.data(s, c) = data(c, s);
    }
  }

  mrd::TrajectoryData traj = acq.trajectory;
  for (uint16_t d = 0; d < hdr.trajectory_dimensions; d++) {
    for (uint16_t s = 0; s < hdr.number_of_samples; s++) {
      acquisition.traj(s, d) = traj(d, s);
    }
  }

  return acquisition;
}

// Convert mrd::Waveform<uint32_t> to ISMRMRD::Waveform
ISMRMRD::Waveform convert(mrd::Waveform<uint32_t>& wfm) {
  ISMRMRD::Waveform waveform(wfm.Channels(), wfm.NumberOfSamples());
  waveform.head.flags = wfm.flags;
  waveform.head.measurement_uid = wfm.measurement_uid;
  waveform.head.scan_counter = wfm.scan_counter;
  waveform.head.time_stamp = wfm.time_stamp_ns / 1e6;      // ns to ms
  waveform.head.sample_time_us = wfm.sample_time_ns / 1e3; // ns to us

  waveform.head.channels = wfm.data.shape()[0];
  waveform.head.number_of_samples = wfm.data.shape()[1];

  for (uint16_t c = 0; c < waveform.head.channels; c++) {
    for (uint16_t s = 0; s < waveform.head.number_of_samples; s++) {
      waveform.data[c * waveform.head.number_of_samples + s] = wfm.data(c, s);
    }
  }

  return waveform;
}

// Convert mrd::Image<T> to ISMRMRD::Image<T>
template <class T>
ISMRMRD::Image<T> convert(mrd::Image<T>& image) {
  ISMRMRD::Image<T> im(image.Cols(), image.Rows(), image.Slices(), image.Channels());

  mrd::ImageHeader& head = image.head;
  im.setFlags(head.flags.Value());
  im.setMeasurementUid(head.measurement_uid);
  im.setFieldOfView(head.field_of_view[0], head.field_of_view[1], head.field_of_view[2]);
  im.setPosition(head.position[0], head.position[1], head.position[2]);
  im.setReadDirection(head.col_dir[0], head.col_dir[1], head.col_dir[2]);
  im.setPhaseDirection(head.line_dir[0], head.line_dir[1], head.line_dir[2]);
  im.setSliceDirection(head.slice_dir[0], head.slice_dir[1], head.slice_dir[2]);
  im.setPatientTablePosition(head.patient_table_position[0], head.patient_table_position[1], head.patient_table_position[2]);
  im.setAverage(head.average.value_or(0));
  im.setSlice(head.slice.value_or(0));
  im.setContrast(head.contrast.value_or(0));
  im.setPhase(head.phase.value_or(0));
  im.setRepetition(head.repetition.value_or(0));
  im.setSet(head.set.value_or(0));
  im.setAcquisitionTimeStamp(head.acquisition_time_stamp_ns.value_or(0) / 1e6); // ns to ms
  for (size_t i = 0; i < ISMRMRD::ISMRMRD_PHYS_STAMPS; i++) {
    if (i < head.physiology_time_stamp_ns.size()) {
      im.setPhysiologyTimeStamp(i, head.physiology_time_stamp_ns[i] / 1e6); // ns to ms
    } else {
      im.setPhysiologyTimeStamp(i, 0);
    }
  }
  switch (head.image_type) {
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
  im.setImageIndex(head.image_index.value_or(0));
  im.setImageSeriesIndex(head.image_series_index.value_or(0));

  if (head.user_int.size() > ISMRMRD::ISMRMRD_USER_INTS) {
    throw std::runtime_error("Too many user_int values");
  }

  for (size_t i = 0; i < head.user_int.size(); i++) {
    im.setUserInt(i, head.user_int[i]);
  }

  if (head.user_float.size() > ISMRMRD::ISMRMRD_USER_FLOATS) {
    throw std::runtime_error("Too many user_float values");
  }

  for (size_t i = 0; i < head.user_float.size(); i++) {
    im.setUserFloat(i, head.user_float[i]);
  }

  ISMRMRD::MetaContainer meta;
  for (auto it = image.meta.begin(); it != image.meta.end(); it++) {
    auto& key = it->first;
    auto& values = it->second;
    for (auto it2 = values.begin(); it2 != values.end(); it2++) {
      mrd::ImageMetaValue& val = *it2;
      if (auto* v = std::get_if<std::string>(&val)) {
        meta.append(key.c_str(), v->c_str());
      } else if (auto* v = std::get_if<int64_t>(&val)) {
        meta.append(key.c_str(), static_cast<long>(*v));
      } else if (auto* v = std::get_if<double>(&val)) {
        meta.append(key.c_str(), *v);
      } else {
        throw std::runtime_error("Unknown meta type");
      }
    }
  }

  std::stringstream ss;
  ISMRMRD::serialize(meta, ss);
  im.setAttributeString(ss.str());

  for (int c = 0; c < im.getNumberOfChannels(); c++) {
    for (int z = 0; z < im.getMatrixSizeZ(); z++) {
      for (int y = 0; y < im.getMatrixSizeY(); y++) {
        for (int x = 0; x < im.getMatrixSizeX(); x++) {
          im(x, y, z, c) = image.data(c, z, y, x);
        }
      }
    }
  }

  return im;
}

ISMRMRD::Image<unsigned short> convert(Image<unsigned short>& im) {
  return convert<unsigned short>(im);
}
ISMRMRD::Image<short> convert(Image<short>& im) {
  return convert<short>(im);
}
ISMRMRD::Image<unsigned int> convert(Image<unsigned int>& im) {
  return convert<unsigned int>(im);
}
ISMRMRD::Image<int> convert(Image<int>& im) {
  return convert<int>(im);
}
ISMRMRD::Image<float> convert(Image<float>& im) {
  return convert<float>(im);
}
ISMRMRD::Image<double> convert(Image<double>& im) {
  return convert<double>(im);
}
ISMRMRD::Image<std::complex<float>> convert(Image<std::complex<float>>& im) {
  return convert<std::complex<float>>(im);
}
ISMRMRD::Image<std::complex<double>> convert(Image<std::complex<double>>& im) {
  return convert<std::complex<double>>(im);
}

// Convert mrd::AcquisitionBucket - no equivalent in ISMRMRD::
int convert(AcquisitionBucket&) {
  return 0;
}

// Convert mrd::ReconData - no equivalent in ISMRMRD::
int convert(ReconData&) {
  return 0;
}

// Convert mrd::ImageArray - no equivalent in ISMRMRD::
int convert(ImageArray&) {
  return 0;
}

// Convert mrd::Array - no equivalent in ISMRMRD::
int convert(ArrayComplexFloat&) {
  return 0;
}

yardl::Date date_from_string(const std::string& s) {
  std::stringstream ss{s};

  date::local_days ld;
  ss >> date::parse("%F", ld);

  if (ss.fail()) {
    throw std::runtime_error("invalid date format");
  }

  yardl::Date d(ld.time_since_epoch());

  return d;
}

yardl::Time time_from_string(const std::string& s) {
  std::stringstream ss{s};
  yardl::Time t;
  ss >> date::parse("%T", t);

  if (ss.fail()) {
    throw std::runtime_error("invalid time format");
  }

  return t;
}

// Convert ISMRMRD::SubjectInformation to mrd::SubjectInformationType
mrd::SubjectInformationType convert(ISMRMRD::SubjectInformation& subjectInformation) {
  mrd::SubjectInformationType s;

  if (subjectInformation.patientName) {
    s.patient_name = *subjectInformation.patientName;
  }

  if (subjectInformation.patientWeight_kg) {
    s.patient_weight_kg = *subjectInformation.patientWeight_kg;
  }

  if (subjectInformation.patientHeight_m) {
    s.patient_height_m = *subjectInformation.patientHeight_m;
  }

  if (subjectInformation.patientID) {
    s.patient_id = *subjectInformation.patientID;
  }

  if (subjectInformation.patientBirthdate) {
    s.patient_birthdate = date_from_string(*subjectInformation.patientBirthdate);
  }

  if (subjectInformation.patientGender) {
    if (*subjectInformation.patientGender == std::string("M")) {
      s.patient_gender = mrd::PatientGender::kM;
    } else if (*subjectInformation.patientGender == std::string("F")) {
      s.patient_gender = mrd::PatientGender::kF;
    } else if (*subjectInformation.patientGender == std::string("O")) {
      s.patient_gender = mrd::PatientGender::kO;
    } else {
      // throw runtime exception
      throw std::runtime_error("Unknown Gender");
    }
  }

  return s;
}

// Convert ISMRMRD::StudyInformation to mrd::StudyInformationType
mrd::StudyInformationType convert(ISMRMRD::StudyInformation& studyInformation) {
  mrd::StudyInformationType s;

  if (studyInformation.studyDate) {
    s.study_date = date_from_string(*studyInformation.studyDate);
  }

  if (studyInformation.studyTime) {
    s.study_time = time_from_string(*studyInformation.studyTime);
  }

  if (studyInformation.studyID) {
    s.study_id = *studyInformation.studyID;
  }

  if (studyInformation.accessionNumber) {
    s.accession_number = *studyInformation.accessionNumber;
  }

  if (studyInformation.referringPhysicianName) {
    s.referring_physician_name = *studyInformation.referringPhysicianName;
  }

  if (studyInformation.studyDescription) {
    s.study_description = *studyInformation.studyDescription;
  }

  if (studyInformation.studyInstanceUID) {
    s.study_instance_uid = *studyInformation.studyInstanceUID;
  }

  if (studyInformation.bodyPartExamined) {
    s.body_part_examined = *studyInformation.bodyPartExamined;
  }

  return s;
}

// Convert ISMRMRD patient position string to mrd::PatientPosition
mrd::PatientPosition patient_position_from_string(std::string& s) {
  if (s == "HFP") {
    return mrd::PatientPosition::kHFP;
  } else if (s == "HFS") {
    return mrd::PatientPosition::kHFS;
  } else if (s == "HFDR") {
    return mrd::PatientPosition::kHFDR;
  } else if (s == "HFDL") {
    return mrd::PatientPosition::kHFDL;
  } else if (s == "FFP") {
    return mrd::PatientPosition::kFFP;
  } else if (s == "FFS") {
    return mrd::PatientPosition::kFFS;
  } else if (s == "FFDR") {
    return mrd::PatientPosition::kFFDR;
  } else if (s == "FFDL") {
    return mrd::PatientPosition::kFFDL;
  } else {
    throw std::runtime_error("Unknown Patient Position");
  }
}

// Convert ISMRMRD::threeDimensionalFloat to mrd::ThreeDimensionalFloat
mrd::ThreeDimensionalFloat convert(ISMRMRD::threeDimensionalFloat& threeDimensionalFloat) {
  mrd::ThreeDimensionalFloat t;
  t.x = threeDimensionalFloat.x;
  t.y = threeDimensionalFloat.y;
  t.z = threeDimensionalFloat.z;
  return t;
}

// Convert ISMRMRD::MeasurementDependency to mrd::MeasurementDependencyType
mrd::MeasurementDependencyType convert(ISMRMRD::MeasurementDependency& measurementDependency) {
  mrd::MeasurementDependencyType m;
  m.measurement_id = measurementDependency.measurementID;
  m.dependency_type = measurementDependency.dependencyType;
  return m;
}

// Convert ISMRMRD::MeasurementInformation to mrd::MeasurementInformationType
mrd::MeasurementInformationType convert(ISMRMRD::MeasurementInformation& measurementInformation) {
  mrd::MeasurementInformationType m;

  if (measurementInformation.measurementID) {
    m.measurement_id = *measurementInformation.measurementID;
  }

  if (measurementInformation.seriesDate) {
    m.series_date = date_from_string(*measurementInformation.seriesDate);
  }

  if (measurementInformation.seriesTime) {
    m.series_time = time_from_string(*measurementInformation.seriesTime);
  }

  m.patient_position = patient_position_from_string(measurementInformation.patientPosition);

  if (measurementInformation.relativeTablePosition) {
    m.relative_table_position = convert(*measurementInformation.relativeTablePosition);
  }

  if (measurementInformation.initialSeriesNumber) {
    m.initial_series_number = *measurementInformation.initialSeriesNumber;
  }

  if (measurementInformation.protocolName) {
    m.protocol_name = *measurementInformation.protocolName;
  }

  if (measurementInformation.sequenceName) {
    m.sequence_name = *measurementInformation.sequenceName;
  }

  if (measurementInformation.seriesDescription) {
    m.series_description = *measurementInformation.seriesDescription;
  }

  for (auto& dependency : measurementInformation.measurementDependency) {
    m.measurement_dependency.push_back(convert(dependency));
  }

  if (measurementInformation.seriesInstanceUIDRoot) {
    m.series_instance_uid_root = *measurementInformation.seriesInstanceUIDRoot;
  }

  if (measurementInformation.frameOfReferenceUID) {
    m.frame_of_reference_uid = *measurementInformation.frameOfReferenceUID;
  }

  if (measurementInformation.referencedImageSequence.size() > 0) {
    mrd::ReferencedImageSequenceType referencedImage;
    for (auto& image : measurementInformation.referencedImageSequence) {
      referencedImage.referenced_sop_instance_uid.push_back(image.referencedSOPInstanceUID);
    }
    m.referenced_image_sequence = referencedImage;
  }

  return m;
}

// Convert ISMRMRD::AcquisitionSystemInformation to mrd::AcquisitionSystemInformationType
mrd::AcquisitionSystemInformationType convert(ISMRMRD::AcquisitionSystemInformation& a) {
  mrd::AcquisitionSystemInformationType asi;

  if (a.systemVendor) {
    asi.system_vendor = *a.systemVendor;
  }

  if (a.systemModel) {
    asi.system_model = *a.systemModel;
  }

  if (a.systemFieldStrength_T) {
    asi.system_field_strength_t = *a.systemFieldStrength_T;
  }

  if (a.relativeReceiverNoiseBandwidth) {
    asi.relative_receiver_noise_bandwidth = *a.relativeReceiverNoiseBandwidth;
  }

  if (a.receiverChannels) {
    asi.receiver_channels = *a.receiverChannels;
  }

  if (a.coilLabel.size() > 0) {
    for (auto& c : a.coilLabel) {
      mrd::CoilLabelType cl;
      cl.coil_name = c.coilName;
      cl.coil_number = c.coilNumber;
      asi.coil_label.push_back(cl);
    }
  }

  if (a.institutionName) {
    asi.institution_name = *a.institutionName;
  }

  if (a.stationName) {
    asi.station_name = *a.stationName;
  }

  if (a.deviceID) {
    asi.device_id = *a.deviceID;
  }

  if (a.deviceSerialNumber) {
    asi.device_serial_number = *a.deviceSerialNumber;
  }

  return asi;
}

// Convert ISMRMRD::ExperimentalConditions to mrd::ExperimentalConditionsType
mrd::ExperimentalConditionsType convert(ISMRMRD::ExperimentalConditions& e) {
  mrd::ExperimentalConditionsType ec;
  ec.h1resonance_frequency_hz = e.H1resonanceFrequency_Hz;
  return ec;
}

// Convert ISMRMRD::MatrixSize to mrd::MatrixSizeType
mrd::MatrixSizeType convert(ISMRMRD::MatrixSize& m) {
  mrd::MatrixSizeType matrixSize;
  matrixSize.x = m.x;
  matrixSize.y = m.y;
  matrixSize.z = m.z;
  return matrixSize;
}

// Convert ISMRMRD::FieldOfView_mm to mrd::FieldOfViewmm
mrd::FieldOfViewMm convert(ISMRMRD::FieldOfView_mm& f) {
  mrd::FieldOfViewMm fieldOfView;
  fieldOfView.x = f.x;
  fieldOfView.y = f.y;
  fieldOfView.z = f.z;
  return fieldOfView;
}

// Convert ISMRMRD::EncodingSpace to mrd::EncodingSpaceType
mrd::EncodingSpaceType convert(ISMRMRD::EncodingSpace& e) {
  mrd::EncodingSpaceType encodingSpace;
  encodingSpace.matrix_size = convert(e.matrixSize);
  encodingSpace.field_of_view_mm = convert(e.fieldOfView_mm);
  return encodingSpace;
}

// Convert ISMRMRD::Limit to mrd::LimitType
mrd::LimitType convert(ISMRMRD::Limit& l) {
  mrd::LimitType limit;
  limit.minimum = l.minimum;
  limit.maximum = l.maximum;
  limit.center = l.center;
  return limit;
}

// Convert ISMRMRD::EncodingLimits to mrd::EncodingLimitsType
mrd::EncodingLimitsType convert(ISMRMRD::EncodingLimits& e) {
  mrd::EncodingLimitsType encodingLimits;

  if (e.kspace_encoding_step_0) {
    encodingLimits.kspace_encoding_step_0 = convert(*e.kspace_encoding_step_0);
  }

  if (e.kspace_encoding_step_1) {
    encodingLimits.kspace_encoding_step_1 = convert(*e.kspace_encoding_step_1);
  }

  if (e.kspace_encoding_step_2) {
    encodingLimits.kspace_encoding_step_2 = convert(*e.kspace_encoding_step_2);
  }

  if (e.average) {
    encodingLimits.average = convert(*e.average);
  }

  if (e.slice) {
    encodingLimits.slice = convert(*e.slice);
  }

  if (e.contrast) {
    encodingLimits.contrast = convert(*e.contrast);
  }

  if (e.phase) {
    encodingLimits.phase = convert(*e.phase);
  }

  if (e.repetition) {
    encodingLimits.repetition = convert(*e.repetition);
  }

  if (e.set) {
    encodingLimits.set = convert(*e.set);
  }

  if (e.segment) {
    encodingLimits.segment = convert(*e.segment);
  }

  if (e.user[0]) {
    encodingLimits.user_0 = convert(*e.user[0]);
  }

  if (e.user[1]) {
    encodingLimits.user_1 = convert(*e.user[1]);
  }

  if (e.user[2]) {
    encodingLimits.user_2 = convert(*e.user[2]);
  }

  if (e.user[3]) {
    encodingLimits.user_3 = convert(*e.user[3]);
  }

  if (e.user[4]) {
    encodingLimits.user_4 = convert(*e.user[4]);
  }

  if (e.user[5]) {
    encodingLimits.user_5 = convert(*e.user[5]);
  }

  if (e.user[6]) {
    encodingLimits.user_6 = convert(*e.user[6]);
  }

  if (e.user[7]) {
    encodingLimits.user_7 = convert(*e.user[7]);
  }

  return encodingLimits;
}

// Convert ISMRMRD::UserParameterLong to mrd::UserParameterLongType
mrd::UserParameterLongType convert(ISMRMRD::UserParameterLong& u) {
  mrd::UserParameterLongType userParameterLong;
  userParameterLong.name = u.name;
  userParameterLong.value = u.value;
  return userParameterLong;
}

// Convert ISMRMRD::UserParameterDouble to mrd::UserParameterDoubleType
mrd::UserParameterDoubleType convert(ISMRMRD::UserParameterDouble& u) {
  mrd::UserParameterDoubleType userParameterDouble;
  userParameterDouble.name = u.name;
  userParameterDouble.value = u.value;
  return userParameterDouble;
}

// Convert ISMRMRD::UserParameterString to mrd::UserParameterStringType
mrd::UserParameterStringType convert(ISMRMRD::UserParameterString& u) {
  mrd::UserParameterStringType userParameterString;
  userParameterString.name = u.name;
  userParameterString.value = u.value;
  return userParameterString;
}

// Convert ISMRMRD::TrajectoryDescription to mrd::TrajectoryDescriptionType
mrd::TrajectoryDescriptionType convert(ISMRMRD::TrajectoryDescription& t) {
  mrd::TrajectoryDescriptionType trajectoryDescription;
  trajectoryDescription.identifier = t.identifier;

  for (auto& u : t.userParameterLong) {
    trajectoryDescription.user_parameter_long.push_back(convert(u));
  }

  for (auto& u : t.userParameterDouble) {
    trajectoryDescription.user_parameter_double.push_back(convert(u));
  }

  for (auto& u : t.userParameterString) {
    trajectoryDescription.user_parameter_string.push_back(convert(u));
  }

  if (t.comment) {
    trajectoryDescription.comment = *t.comment;
  }

  return trajectoryDescription;
}

// Convert ISMRMRD::AccelerationFactor to mrd::AccelerationFactorType
mrd::AccelerationFactorType convert(ISMRMRD::AccelerationFactor& a) {
  mrd::AccelerationFactorType accelerationFactor;
  accelerationFactor.kspace_encoding_step_1 = a.kspace_encoding_step_1;
  accelerationFactor.kspace_encoding_step_2 = a.kspace_encoding_step_2;
  return accelerationFactor;
}

// Convert ISMRMRD calibration mode string to mrd::CalibrationMode
mrd::CalibrationMode calibration_mode_from_string(std::string& m) {
  if (m == "embedded") {
    return mrd::CalibrationMode::kEmbedded;
  } else if (m == "interleaved") {
    return mrd::CalibrationMode::kInterleaved;
  } else if (m == "separate") {
    return mrd::CalibrationMode::kSeparate;
  } else if (m == "external") {
    return mrd::CalibrationMode::kExternal;
  } else if (m == "other") {
    return mrd::CalibrationMode::kOther;
  } else {
    throw std::runtime_error("Unknown CalibrationMode: " + m);
  }
}

// Convert ISMRMRD interleaving dimension string to mrd::InterleavingDimension
mrd::InterleavingDimension interleaving_dimension_from_string(std::string& s) {
  if (s == "phase") {
    return mrd::InterleavingDimension::kPhase;
  } else if (s == "repetition") {
    return mrd::InterleavingDimension::kRepetition;
  } else if (s == "contrast") {
    return mrd::InterleavingDimension::kContrast;
  } else if (s == "average") {
    return mrd::InterleavingDimension::kAverage;
  } else if (s == "other") {
    return mrd::InterleavingDimension::kOther;
  } else {
    throw std::runtime_error("Unknown InterleavingDimension: " + s);
  }
}

// Convert ISMRMRD::MultibandSpacing to mrd::MultibandSpacingType
mrd::MultibandSpacingType convert(ISMRMRD::MultibandSpacing& m) {
  mrd::MultibandSpacingType multibandSpacing;
  for (auto s : m.dZ) {
    multibandSpacing.d_z.push_back(s);
  }
  return multibandSpacing;
}

// Convert ISMRMRD::MultibandCalibrationType to mrd::Calibration
mrd::Calibration convert(ISMRMRD::MultibandCalibrationType& m) {
  switch (m) {
  case ISMRMRD::MultibandCalibrationType::SEPARABLE2D:
    return mrd::Calibration::kSeparable2D;
  case ISMRMRD::MultibandCalibrationType::FULL3D:
    return mrd::Calibration::kFull3D;
  case ISMRMRD::MultibandCalibrationType::OTHER:
    return mrd::Calibration::kOther;
  default:
    throw std::runtime_error("Unknown Calibration");
  }
}

// Convert ISMRMRD::Multiband to mrd::MultibandType
mrd::MultibandType convert(ISMRMRD::Multiband& m) {
  mrd::MultibandType multiband;
  for (auto s : m.spacing) {
    multiband.spacing.push_back(convert(s));
  }
  multiband.delta_kz = m.deltaKz;
  multiband.multiband_factor = m.multiband_factor;
  multiband.calibration = convert(m.calibration);
  multiband.calibration_encoding = m.calibration_encoding;
  return multiband;
}

// Convert ISMRMRD::ParallelImaging to mrd::ParallelImagingType
mrd::ParallelImagingType convert(ISMRMRD::ParallelImaging& p) {
  mrd::ParallelImagingType parallelImaging;
  parallelImaging.acceleration_factor = convert(p.accelerationFactor);
  if (p.calibrationMode) {
    parallelImaging.calibration_mode = calibration_mode_from_string(*p.calibrationMode);
  }
  if (p.interleavingDimension) {
    parallelImaging.interleaving_dimension = interleaving_dimension_from_string(*p.interleavingDimension);
  }
  if (p.multiband) {
    parallelImaging.multiband = convert(*p.multiband);
  }
  return parallelImaging;
}

// Convert ISMRMRD::Encoding to mrd::EncodingType
mrd::EncodingType convert(ISMRMRD::Encoding& e) {
  mrd::EncodingType encoding;

  encoding.encoded_space = convert(e.encodedSpace);
  encoding.recon_space = convert(e.reconSpace);
  encoding.encoding_limits = convert(e.encodingLimits);

  switch (e.trajectory) {
  case ISMRMRD::TrajectoryType::CARTESIAN:
    encoding.trajectory = mrd::Trajectory::kCartesian;
    break;
  case ISMRMRD::TrajectoryType::EPI:
    encoding.trajectory = mrd::Trajectory::kEpi;
    break;
  case ISMRMRD::TrajectoryType::RADIAL:
    encoding.trajectory = mrd::Trajectory::kRadial;
    break;
  case ISMRMRD::TrajectoryType::GOLDENANGLE:
    encoding.trajectory = mrd::Trajectory::kGoldenangle;
    break;
  case ISMRMRD::TrajectoryType::SPIRAL:
    encoding.trajectory = mrd::Trajectory::kSpiral;
    break;
  case ISMRMRD::TrajectoryType::OTHER:
    encoding.trajectory = mrd::Trajectory::kOther;
    break;
  default:
    throw std::runtime_error("Unknown TrajectoryType");
  }

  if (e.trajectoryDescription) {
    encoding.trajectory_description = convert(*e.trajectoryDescription);
  }

  if (e.parallelImaging) {
    encoding.parallel_imaging = convert(*e.parallelImaging);
  }

  if (e.echoTrainLength) {
    encoding.echo_train_length = *e.echoTrainLength;
  }

  return encoding;
}

// Convert ISMRMRD::DiffusionDimension to mrd::DiffusionDimension
mrd::DiffusionDimension convert(ISMRMRD::DiffusionDimension& diffusionDimension) {
  switch (diffusionDimension) {
  case ISMRMRD::DiffusionDimension::AVERAGE:
    return mrd::DiffusionDimension::kAverage;
  case ISMRMRD::DiffusionDimension::CONTRAST:
    return mrd::DiffusionDimension::kContrast;
  case ISMRMRD::DiffusionDimension::PHASE:
    return mrd::DiffusionDimension::kPhase;
  case ISMRMRD::DiffusionDimension::REPETITION:
    return mrd::DiffusionDimension::kRepetition;
  case ISMRMRD::DiffusionDimension::SET:
    return mrd::DiffusionDimension::kSet;
  case ISMRMRD::DiffusionDimension::SEGMENT:
    return mrd::DiffusionDimension::kSegment;
  case ISMRMRD::DiffusionDimension::USER_0:
    return mrd::DiffusionDimension::kUser0;
  case ISMRMRD::DiffusionDimension::USER_1:
    return mrd::DiffusionDimension::kUser1;
  case ISMRMRD::DiffusionDimension::USER_2:
    return mrd::DiffusionDimension::kUser2;
  case ISMRMRD::DiffusionDimension::USER_3:
    return mrd::DiffusionDimension::kUser3;
  case ISMRMRD::DiffusionDimension::USER_4:
    return mrd::DiffusionDimension::kUser4;
  case ISMRMRD::DiffusionDimension::USER_5:
    return mrd::DiffusionDimension::kUser5;
  case ISMRMRD::DiffusionDimension::USER_6:
    return mrd::DiffusionDimension::kUser6;
  case ISMRMRD::DiffusionDimension::USER_7:
    return mrd::DiffusionDimension::kUser7;
  default:
    throw std::runtime_error("Unknown diffusion dimension");
  }
}

// Convert ISMRMRD::GradientDirection to mrd::GradientDirectionType
mrd::GradientDirectionType convert(ISMRMRD::GradientDirection& g) {
  mrd::GradientDirectionType gradientDirection;
  gradientDirection.rl = g.rl;
  gradientDirection.ap = g.ap;
  gradientDirection.fh = g.fh;
  return gradientDirection;
}

// Convert ISMRMRD::Diffusion to mrd::DiffusionType
mrd::DiffusionType convert(ISMRMRD::Diffusion& d) {
  mrd::DiffusionType diffusion;
  diffusion.gradient_direction = convert(d.gradientDirection);
  diffusion.bvalue = d.bvalue;
  return diffusion;
}

// Convert ISMRMRD::SequenceParameters to mrd::SequenceParametersType
mrd::SequenceParametersType convert(ISMRMRD::SequenceParameters& s) {
  mrd::SequenceParametersType sequenceParameters;

  if (s.TR) {
    for (auto& t : *s.TR) {
      sequenceParameters.t_r.push_back(t);
    }
  }

  if (s.TE) {
    for (auto& t : *s.TE) {
      sequenceParameters.t_e.push_back(t);
    }
  }

  if (s.TI) {
    for (auto& t : *s.TI) {
      sequenceParameters.t_i.push_back(t);
    }
  }

  if (s.flipAngle_deg) {
    for (auto& t : *s.flipAngle_deg) {
      sequenceParameters.flip_angle_deg.push_back(t);
    }
  }

  if (s.sequence_type) {
    sequenceParameters.sequence_type = *s.sequence_type;
  }

  if (s.echo_spacing) {
    for (auto& t : *s.echo_spacing) {
      sequenceParameters.echo_spacing.push_back(t);
    }
  }

  if (s.diffusionDimension) {
    sequenceParameters.diffusion_dimension = convert(*s.diffusionDimension);
  }

  if (s.diffusion) {
    for (auto& d : *s.diffusion) {
      sequenceParameters.diffusion.push_back(convert(d));
    }
  }

  if (s.diffusionScheme) {
    sequenceParameters.diffusion_scheme = *s.diffusionScheme;
  }

  return sequenceParameters;
}

// Convert ISMRMRD::UserParameterString to mrd::UserParameterBase64Type
mrd::UserParameterBase64Type convert_userbase64(ISMRMRD::UserParameterString& u) {
  mrd::UserParameterBase64Type userParameterBase64;
  userParameterBase64.name = u.name;
  userParameterBase64.value = u.value;
  return userParameterBase64;
}

// Convert ISMRMRD::UserParameters to mrd::UserParametersType
mrd::UserParametersType convert(ISMRMRD::UserParameters& u) {
  mrd::UserParametersType userParameters;

  for (auto& p : u.userParameterLong) {
    userParameters.user_parameter_long.push_back(convert(p));
  }

  for (auto& p : u.userParameterDouble) {
    userParameters.user_parameter_double.push_back(convert(p));
  }

  for (auto& p : u.userParameterString) {
    userParameters.user_parameter_string.push_back(convert(p));
  }

  for (auto& p : u.userParameterBase64) {
    userParameters.user_parameter_base64.push_back(convert_userbase64(p));
  }

  return userParameters;
}

// Convert ISMRMRD::WaveformType to mrd::WaveformType
mrd::WaveformType convert(ISMRMRD::WaveformType& w) {
  switch (w) {
  case ISMRMRD::WaveformType::ECG:
    return mrd::WaveformType::kEcg;
  case ISMRMRD::WaveformType::PULSE:
    return mrd::WaveformType::kPulse;
  case ISMRMRD::WaveformType::RESPIRATORY:
    return mrd::WaveformType::kRespiratory;
  case ISMRMRD::WaveformType::TRIGGER:
    return mrd::WaveformType::kTrigger;
  case ISMRMRD::WaveformType::GRADIENTWAVEFORM:
    return mrd::WaveformType::kGradientwaveform;
  case ISMRMRD::WaveformType::OTHER:
    return mrd::WaveformType::kOther;
  default:
    throw std::runtime_error("Unknown waveform type");
  }
}

// Convert ISMRMRD::WaveformInformation to mrd::WaveformInformationType
mrd::WaveformInformationType convert(ISMRMRD::WaveformInformation& w) {
  mrd::WaveformInformationType waveformInformation;
  waveformInformation.waveform_name = w.waveformName;
  waveformInformation.waveform_type = convert(w.waveformType);
  if (w.userParameters) {
    waveformInformation.user_parameters = convert(*w.userParameters);
  }
  return waveformInformation;
}

// Convert ISMRMMRD::IsmrmrdHeader to mrd::Header
mrd::Header convert(ISMRMRD::IsmrmrdHeader& hdr) {
  mrd::Header h;

  if (hdr.version) {
    h.version = *hdr.version;
  }

  if (hdr.subjectInformation) {
    h.subject_information = convert(*hdr.subjectInformation);
  }

  if (hdr.studyInformation) {
    h.study_information = convert(*hdr.studyInformation);
  }

  if (hdr.measurementInformation) {
    h.measurement_information = convert(*hdr.measurementInformation);
  }

  if (hdr.acquisitionSystemInformation) {
    h.acquisition_system_information = convert(*hdr.acquisitionSystemInformation);
  }

  h.experimental_conditions = convert(hdr.experimentalConditions);

  if (hdr.encoding.size() > 0) {
    for (auto e : hdr.encoding) {
      h.encoding.push_back(convert(e));
    }
  } else {
    throw std::runtime_error("No encoding found in ISMRMRD header");
  }

  if (hdr.sequenceParameters) {
    h.sequence_parameters = convert(*hdr.sequenceParameters);
  }

  if (hdr.userParameters) {
    h.user_parameters = convert(*hdr.userParameters);
  }

  for (auto w : hdr.waveformInformation) {
    h.waveform_information.push_back(convert(w));
  }

  return h;
}

// Convert ISMRMRD::EncodingCounters to mrd::EncodingCounters
mrd::EncodingCounters convert(ISMRMRD::EncodingCounters& e) {
  mrd::EncodingCounters encodingCounters;
  encodingCounters.kspace_encode_step_1 = e.kspace_encode_step_1;
  encodingCounters.kspace_encode_step_2 = e.kspace_encode_step_2;
  encodingCounters.average = e.average;
  encodingCounters.slice = e.slice;
  encodingCounters.contrast = e.contrast;
  encodingCounters.phase = e.phase;
  encodingCounters.repetition = e.repetition;
  encodingCounters.set = e.set;
  encodingCounters.segment = e.segment;
  for (auto& u : e.user) {
    encodingCounters.user.push_back(u);
  }

  return encodingCounters;
}

// Convert ISMRMRD::Acquisition to mrd::Acquisition
mrd::Acquisition convert(ISMRMRD::Acquisition& acq) {
  mrd::Acquisition acquisition;

  acquisition.head.flags = acq.flags();
  acquisition.head.idx = convert(acq.idx());
  acquisition.head.measurement_uid = acq.measurement_uid();
  acquisition.head.scan_counter = acq.scan_counter();
  acquisition.head.acquisition_time_stamp_ns = acq.acquisition_time_stamp() * 1e6; // ms to ns
  for (auto& p : acq.physiology_time_stamp()) {
    acquisition.head.physiology_time_stamp_ns.push_back(p * 1e6); // ms to ns
  }

  for (size_t i = 0; i < acq.active_channels(); i++) {
    acquisition.head.channel_order.push_back(i);
  }

  acquisition.head.discard_pre = acq.discard_pre();
  acquisition.head.discard_post = acq.discard_post();
  acquisition.head.center_sample = acq.center_sample();
  acquisition.head.encoding_space_ref = acq.encoding_space_ref();
  acquisition.head.sample_time_ns = acq.sample_time_us() * 1e3; // us to ns

  acquisition.head.position[0] = acq.position()[0];
  acquisition.head.position[1] = acq.position()[1];
  acquisition.head.position[2] = acq.position()[2];

  acquisition.head.read_dir[0] = acq.read_dir()[0];
  acquisition.head.read_dir[1] = acq.read_dir()[1];
  acquisition.head.read_dir[2] = acq.read_dir()[2];

  acquisition.head.phase_dir[0] = acq.phase_dir()[0];
  acquisition.head.phase_dir[1] = acq.phase_dir()[1];
  acquisition.head.phase_dir[2] = acq.phase_dir()[2];

  acquisition.head.slice_dir[0] = acq.slice_dir()[0];
  acquisition.head.slice_dir[1] = acq.slice_dir()[1];
  acquisition.head.slice_dir[2] = acq.slice_dir()[2];

  acquisition.head.patient_table_position[0] = acq.patient_table_position()[0];
  acquisition.head.patient_table_position[1] = acq.patient_table_position()[1];
  acquisition.head.patient_table_position[2] = acq.patient_table_position()[2];

  for (auto& p : acq.user_int()) {
    acquisition.head.user_int.push_back(p);
  }
  for (auto& p : acq.user_float()) {
    acquisition.head.user_float.push_back(p);
  }

  acquisition.data.resize({acq.active_channels(), acq.number_of_samples()});
  for (uint16_t c = 0; c < acq.active_channels(); c++) {
    for (uint16_t s = 0; s < acq.number_of_samples(); s++) {
      acquisition.data(c, s) = acq.data(s, c);
    }
  }

  if (acq.trajectory_dimensions() > 0) {
    acquisition.trajectory.resize({acq.trajectory_dimensions(), acq.number_of_samples()});
    for (uint16_t d = 0; d < acq.trajectory_dimensions(); d++) {
      for (uint16_t s = 0; s < acq.number_of_samples(); s++) {
        acquisition.trajectory(d, s) = acq.traj(s, d);
      }
    }
  }

  return acquisition;
}

// Convert ISMRMRD::Waveform to mrd::Waveform
mrd::Waveform<uint32_t> convert(ISMRMRD::Waveform& wfm) {
  mrd::Waveform<uint32_t> waveform;
  waveform.flags = wfm.head.flags;
  waveform.measurement_uid = wfm.head.measurement_uid;
  waveform.scan_counter = wfm.head.scan_counter;
  waveform.time_stamp_ns = wfm.head.time_stamp * 1e6;      // ms to ns
  waveform.sample_time_ns = wfm.head.sample_time_us * 1e3; // us to ns

  mrd::WaveformSamples<uint32_t> data({wfm.head.channels, wfm.head.number_of_samples});
  for (uint16_t c = 0; c < wfm.head.channels; c++) {
    for (uint16_t s = 0; s < wfm.head.number_of_samples; s++) {
      data(c, s) = wfm.data[c * wfm.head.number_of_samples + s];
    }
  }

  waveform.data = xt::view(data, xt::all(), xt::all());
  return waveform;
}

// Convert mrd::Image<T> to ISMRMRD::Image<T>
template <typename T>
mrd::Image<T> convert(ISMRMRD::Image<T>& im) {
  mrd::Image<T> image;
  image.head.flags = im.getFlags();
  image.head.measurement_uid = im.getMeasurementUid();
  image.head.field_of_view[0] = im.getFieldOfViewX();
  image.head.field_of_view[1] = im.getFieldOfViewY();
  image.head.field_of_view[2] = im.getFieldOfViewZ();
  image.head.position[0] = im.getPositionX();
  image.head.position[1] = im.getPositionY();
  image.head.position[2] = im.getPositionZ();
  image.head.col_dir[0] = im.getReadDirectionX();
  image.head.col_dir[1] = im.getReadDirectionY();
  image.head.col_dir[2] = im.getReadDirectionZ();
  image.head.line_dir[0] = im.getPhaseDirectionX();
  image.head.line_dir[1] = im.getPhaseDirectionY();
  image.head.line_dir[2] = im.getPhaseDirectionZ();
  image.head.slice_dir[0] = im.getSliceDirectionX();
  image.head.slice_dir[1] = im.getSliceDirectionY();
  image.head.slice_dir[2] = im.getSliceDirectionZ();
  image.head.patient_table_position[0] = im.getPatientTablePositionX();
  image.head.patient_table_position[1] = im.getPatientTablePositionY();
  image.head.patient_table_position[2] = im.getPatientTablePositionZ();
  image.head.average = im.getAverage();
  image.head.slice = im.getSlice();
  image.head.contrast = im.getContrast();
  image.head.phase = im.getPhase();
  image.head.repetition = im.getRepetition();
  image.head.set = im.getSet();
  image.head.acquisition_time_stamp_ns = im.getAcquisitionTimeStamp() * 1e6;         // ms to ns
  image.head.physiology_time_stamp_ns.push_back(im.getPhysiologyTimeStamp(0) * 1e6); // ms to ns
  image.head.physiology_time_stamp_ns.push_back(im.getPhysiologyTimeStamp(1) * 1e6); // ms to ns
  image.head.physiology_time_stamp_ns.push_back(im.getPhysiologyTimeStamp(2) * 1e6); // ms to ns

  if (im.getImageType() == ISMRMRD::ISMRMRD_ImageTypes::ISMRMRD_IMTYPE_COMPLEX) {
    image.head.image_type = mrd::ImageType::kComplex;
  } else if (im.getImageType() == ISMRMRD::ISMRMRD_ImageTypes::ISMRMRD_IMTYPE_MAGNITUDE) {
    image.head.image_type = mrd::ImageType::kMagnitude;
  } else if (im.getImageType() == ISMRMRD::ISMRMRD_ImageTypes::ISMRMRD_IMTYPE_REAL) {
    image.head.image_type = mrd::ImageType::kReal;
  } else if (im.getImageType() == ISMRMRD::ISMRMRD_ImageTypes::ISMRMRD_IMTYPE_PHASE) {
    image.head.image_type = mrd::ImageType::kPhase;
  } else if (im.getImageType() == ISMRMRD::ISMRMRD_ImageTypes::ISMRMRD_IMTYPE_IMAG) {
    image.head.image_type = mrd::ImageType::kImag;
  } else {
    throw std::runtime_error("Unknown image type");
  }

  image.head.image_index = im.getImageIndex();
  image.head.image_series_index = im.getImageSeriesIndex();
  for (int i = 0; i < ISMRMRD::ISMRMRD_USER_INTS; i++) {
    image.head.user_int.push_back(im.getUserInt(i));
  }
  for (int i = 0; i < ISMRMRD::ISMRMRD_USER_FLOATS; i++) {
    image.head.user_float.push_back(im.getUserFloat(i));
  }

  mrd::ImageData<T> data({im.getNumberOfChannels(), im.getMatrixSizeZ(), im.getMatrixSizeY(), im.getMatrixSizeX()});
  for (int c = 0; c < im.getNumberOfChannels(); c++) {
    for (int z = 0; z < im.getMatrixSizeZ(); z++) {
      for (int y = 0; y < im.getMatrixSizeY(); y++) {
        for (int x = 0; x < im.getMatrixSizeX(); x++) {
          data(c, z, y, x) = im(x, y, z, c);
        }
      }
    }
  }

  image.data = xt::view(data, xt::all(), xt::all(), xt::all(), xt::all());

  std::string attrib;
  im.getAttributeString(attrib);
  if (attrib.length() > 0) {
    ISMRMRD::MetaContainer meta;
    ISMRMRD::deserialize(attrib.c_str(), meta);
    for (auto it = meta.begin(); it != meta.end(); it++) {
      for (auto it2 = it->second.begin(); it2 != it->second.end(); it2++) {
        image.meta[it->first].push_back(it2->as_str());
      }
    }
  }

  return image;
}

Image<unsigned short> convert(ISMRMRD::Image<unsigned short>& im) {
  return convert<unsigned short>(im);
}
Image<short> convert(ISMRMRD::Image<short>& im) {
  return convert<short>(im);
}
Image<unsigned int> convert(ISMRMRD::Image<unsigned int>& im) {
  return convert<unsigned int>(im);
}
Image<int> convert(ISMRMRD::Image<int>& im) {
  return convert<int>(im);
}
Image<float> convert(ISMRMRD::Image<float>& im) {
  return convert<float>(im);
}
Image<double> convert(ISMRMRD::Image<double>& im) {
  return convert<double>(im);
}
Image<std::complex<float>> convert(ISMRMRD::Image<std::complex<float>>& im) {
  return convert<std::complex<float>>(im);
}
Image<std::complex<double>> convert(ISMRMRD::Image<std::complex<double>>& im) {
  return convert<std::complex<double>>(im);
}

}

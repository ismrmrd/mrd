#include "fftw_wrappers.h"
#include "mrd/binary/protocols.h"
#include "shepp_logan_phantom.h"

#include <iostream>
#include <random>
#include <xtensor/generators/xrandom.hpp>
#include <xtensor/views/xview.hpp>

using namespace mrd;

xt::xtensor<std::complex<float>, 4> fftshift(xt::xtensor<std::complex<float>, 4> x) {
  return xt::roll(xt::roll(x, x.shape(3) / 2, 3), x.shape(2) / 2, 2);
}

template <std::size_t N>
xt::xtensor<std::complex<float>, N> generate_noise(std::array<size_t, N> shape, float sigma, float mean = 0.0) {
  using namespace std::complex_literals;
  if (sigma > 0.0f) {
    return xt::random::randn(shape, mean, sigma) + 1.0i * xt::random::randn(shape, mean, sigma);
  } else {
    return xt::zeros<std::complex<float>>(shape);
  }
}

int main(int argc, char** argv) {
  uint32_t matrix = 256;
  uint32_t ncoils = 8;
  uint32_t repetitions = 1;
  uint32_t acc_factor = 1;
  uint32_t oversampling = 2;
  float noise_level = 0.05;
  uint32_t calib_width = 0;
  bool add_noise_calibration = false;
  bool store_coordinates = false;
  std::string filename;

  auto bool2str = [](bool b) { return b ? "true" : "false"; };

  auto print_usage = [&]() {
    std::cerr << "Usage: " << argv[0] << std::endl;
    std::cerr << "  -h|--help" << std::endl;
    std::cerr << "  -o|--output       <output stream>   (default: stdout)" << std::endl;
    std::cerr << "  -c|--coils        <number of coils> (default: " << ncoils << ")" << std::endl;
    std::cerr << "  -m|--matrix       <matrix size>     (default: " << matrix << ")" << std::endl;
    std::cerr << "  -r|--repetitions  <repetitions>     (default: " << repetitions << ")" << std::endl;
    std::cerr << "  -a|--acceleration <acceleration>    (default: " << acc_factor << ")" << std::endl;
    std::cerr << "  -s|--oversampling <oversampling>    (default: " << oversampling << ")" << std::endl;
    std::cerr << "  -n|--noise-level  <noise level>     (default: " << noise_level << ")" << std::endl;
    std::cerr << "  -w|--calibration-width  <calibration width>         (default: " << calib_width << ")" << std::endl;
    std::cerr << "  -C|--noise-calibration  <add noise calibration>     (default: " << bool2str(add_noise_calibration) << ")" << std::endl;
    std::cerr << "  -K|--store-coordinates  <add k-space coordinates>   (default: " << bool2str(store_coordinates) << ")" << std::endl;
    std::cerr << "  --output-phantom <filename> (write raw phantom array to file)" << std::endl;
    std::cerr << "  --output-csm <filename> (write coil sensitivities array to file)" << std::endl;
    std::cerr << "  --output-coils <filename> (write coil image array to file)" << std::endl;
  };

  std::string output_phantom_filename;
  std::string output_csm_filename;
  std::string output_coils_filename;

  std::vector<std::string> args(argv, argv + argc);
  auto current_arg = args.begin() + 1;
  while (current_arg != args.end()) {
    if (*current_arg == "--help" || *current_arg == "-h") {
      print_usage();
      return 0;
    } else if (*current_arg == "--output" || *current_arg == "-o") {
      current_arg++;
      if (current_arg == args.end()) {
        std::cerr << "Missing output file" << std::endl;
        print_usage();
        return 1;
      }
      filename = *current_arg;
      current_arg++;
    } else if (*current_arg == "--coils" || *current_arg == "-c") {
      current_arg++;
      if (current_arg == args.end()) {
        std::cerr << "Missing number of coils" << std::endl;
        print_usage();
        return 1;
      }
      ncoils = std::stoi(*current_arg);
      current_arg++;
    } else if (*current_arg == "--matrix" || *current_arg == "-m") {
      current_arg++;
      if (current_arg == args.end()) {
        std::cerr << "Missing matrix size" << std::endl;
        print_usage();
        return 1;
      }
      matrix = std::stoi(*current_arg);
      current_arg++;
    } else if (*current_arg == "--repetitions" || *current_arg == "-r") {
      current_arg++;
      if (current_arg == args.end()) {
        std::cerr << "Missing number of frames" << std::endl;
        print_usage();
        return 1;
      }
      repetitions = std::stoi(*current_arg);
      current_arg++;
    } else if (*current_arg == "--acceleration" || *current_arg == "-a") {
      current_arg++;
      if (current_arg == args.end()) {
        std::cerr << "Missing acceleration factor" << std::endl;
        print_usage();
        return 1;
      }
      acc_factor = std::stoi(*current_arg);
      current_arg++;
    } else if (*current_arg == "--oversampling" || *current_arg == "-s") {
      current_arg++;
      if (current_arg == args.end()) {
        std::cerr << "Missing oversampling factor" << std::endl;
        print_usage();
        return 1;
      }
      oversampling = std::stoi(*current_arg);
      current_arg++;
    } else if (*current_arg == "--noise-level" || *current_arg == "-n") {
      current_arg++;
      if (current_arg == args.end()) {
        std::cerr << "Missing noise level" << std::endl;
        print_usage();
        return 1;
      }
      noise_level = std::stof(*current_arg);
      current_arg++;
    } else if (*current_arg == "--calibration-width" || *current_arg == "-w") {
      current_arg++;
      if (current_arg == args.end()) {
        std::cerr << "Missing calibration width" << std::endl;
        print_usage();
        return 1;
      }
      calib_width = std::stoi(*current_arg);
      current_arg++;
    } else if (*current_arg == "--noise-calibration" || *current_arg == "-C") {
      current_arg++;
      add_noise_calibration = true;
    } else if (*current_arg == "--store-coordinates" || *current_arg == "-K") {
      current_arg++;
      store_coordinates = true;
    } else if (*current_arg == "--output-phantom") {
      current_arg++;
      if (current_arg == args.end()) {
        std::cerr << "Missing output phantom file" << std::endl;
        print_usage();
        return 1;
      }
      output_phantom_filename = *current_arg;
      current_arg++;
    } else if (*current_arg == "--output-csm") {
      current_arg++;
      if (current_arg == args.end()) {
        std::cerr << "Missing output csm file" << std::endl;
        print_usage();
        return 1;
      }
      output_csm_filename = *current_arg;
      current_arg++;
    } else if (*current_arg == "--output-coils") {
      current_arg++;
      if (current_arg == args.end()) {
        std::cerr << "Missing output coils file" << std::endl;
        print_usage();
        return 1;
      }
      output_coils_filename = *current_arg;
      current_arg++;
    } else {
      std::cerr << "Unknown argument: " << *current_arg << std::endl;
      print_usage();
      return 1;
    }
  }

  std::unique_ptr<MrdWriterBase> w;

  if (filename.empty()) {
    w = std::make_unique<mrd::binary::MrdWriter>(std::cout);
  } else {
    w = std::make_unique<mrd::binary::MrdWriter>(filename);
  }

  // Parameters
  auto nx = matrix;
  auto ny = matrix;
  auto nkx = oversampling * matrix;
  auto nky = ny;
  float fov = 300;
  float slice_thickness = 5;

  Header h;
  SubjectInformationType subject;
  subject.patient_id = "1234BGVF";
  subject.patient_name = "John Doe";
  h.subject_information = subject;

  MeasurementInformationType measInfo;
  measInfo.patient_position = PatientPosition::kHFS;
  h.measurement_information = measInfo;

  AcquisitionSystemInformationType sys;
  sys.receiver_channels = ncoils;
  for (unsigned int c = 0; c < ncoils; c++) {
    sys.coil_label.push_back(CoilLabelType{c, "Channel " + std::to_string(c)});
  }
  h.acquisition_system_information = sys;

  ExperimentalConditionsType exp;
  exp.h1resonance_frequency_hz = 128000000;
  h.experimental_conditions = exp;

  EncodingSpaceType e;
  e.matrix_size = {nkx, nky, 1};
  e.field_of_view_mm = {oversampling * fov, fov, slice_thickness};

  EncodingSpaceType r;
  r.matrix_size = {nx, ny, 1};
  r.field_of_view_mm = {fov, fov, slice_thickness};

  LimitType limits1;
  limits1.minimum = 0;
  limits1.center = ny / 2;
  limits1.maximum = ny - 1;

  LimitType limits_rep;
  limits_rep.minimum = 0;
  limits_rep.center = repetitions / 2;
  limits_rep.maximum = repetitions - 1;

  EncodingLimitsType limits;
  limits.kspace_encoding_step_1 = limits1;
  limits.repetition = limits_rep;

  EncodingType enc;
  enc.trajectory = Trajectory::kCartesian;
  enc.encoded_space = e;
  enc.recon_space = r;
  enc.encoding_limits = limits;

  if (acc_factor > 1) {
    ParallelImagingType p;
    p.acceleration_factor.kspace_encoding_step_1 = acc_factor;
    p.acceleration_factor.kspace_encoding_step_2 = 1;
    p.calibration_mode = mrd::CalibrationMode::kEmbedded;
    enc.parallel_imaging = p;
  }

  h.encoding.push_back(enc);

  w->WriteHeader(h);

  // We will reuse this Acquisition object
  Acquisition acq;

  std::array<size_t, 2> acq_shape = {ncoils, nkx};
  acq.data.resize(acq_shape);
  for (unsigned int c = 0; c < ncoils; c++) {
    acq.head.channel_order.push_back(c);
  }

  acq.head.center_sample = nkx / 2;
  acq.head.encoding_space_ref = 0;
  acq.head.sample_time_ns = 5000;

  acq.head.read_dir[0] = 1.0;
  acq.head.phase_dir[1] = 1.0;
  acq.head.slice_dir[2] = 1.0;

  uint32_t scan_counter = 0;

  if (add_noise_calibration) {
    // Write a few noise scans
    for (unsigned int n = 0; n < 32; n++) {
      std::array<size_t, 2> noise_shape = {ncoils, nkx};
      auto noise = generate_noise(noise_shape, noise_level);
      acq.head.scan_counter = scan_counter++;
      acq.head.flags |= static_cast<uint64_t>(AcquisitionFlags::kIsNoiseMeasurement);
      xt::view(acq.data, xt::all(), xt::all()) = noise;
      w->WriteData(acq);
    }
  }

  // Generate phantom k-space
  xt::xtensor<std::complex<float>, 4> coil_images;
  {
    xt::xtensor<std::complex<float>, 4> phantom = shepp_logan_phantom(matrix);
    xt::xtensor<std::complex<float>, 4> csm = generate_birdcage_sensitivities(matrix, ncoils, 1.5);

    coil_images = phantom * csm;

    // Simulate oversampling
    if (oversampling > 1) {
      std::array<size_t, 4> padded_shape = coil_images.shape();
      padded_shape[3] *= oversampling;
      xt::xtensor<std::complex<float>, 4> padded = xt::zeros<std::complex<float>>(padded_shape);
      auto pad = (oversampling - 1) * matrix / 2;
      xt::view(padded, xt::all(), xt::all(), xt::all(), xt::range(pad, pad + matrix)) = coil_images;
      coil_images = padded;
    }

    auto serialize_array = [&h](const std::string& filename, const xt::xtensor<std::complex<float>, 4>& arr) {
      mrd::binary::MrdWriter w(filename);
      w.WriteHeader(h);
      w.WriteData(arr);
      w.EndData();
      w.Close();
    };

    if (!output_phantom_filename.empty()) {
      serialize_array(output_phantom_filename, phantom);
    }

    if (!output_csm_filename.empty()) {
      serialize_array(output_csm_filename, csm);
    }

    if (!output_coils_filename.empty()) {
      serialize_array(output_coils_filename, coil_images);
    }
  }

  // Apply FFT
  coil_images = fftshift(coil_images);
  for (unsigned int c = 0; c < ncoils; c++) {
    auto tmp1 = fftw_wrappers::fft2(xt::xarray<std::complex<float>>(xt::view(coil_images, c, 0, xt::all(), xt::all())));
    tmp1 /= std::sqrt(1.0f * tmp1.size());
    xt::view(coil_images, c, 0, xt::all(), xt::all()) = tmp1;
  }
  coil_images = fftshift(coil_images);

  size_t calib_start = nky / 2 - calib_width / 2;

  // Write out Acquisitions
  for (unsigned int r = 0; r < repetitions; r++) {
    auto noise = generate_noise(coil_images.shape(), noise_level);
    auto kspace = xt::xtensor<std::complex<float>, 4>(coil_images) + noise;
    auto a = r % acc_factor;
    for (size_t line = 0; line < nky; line++) {

      bool is_sampled_line = ((line - a) % acc_factor) == 0;
      bool in_calibration_region = (line >= calib_start && line < (calib_start + calib_width));
      if (!is_sampled_line && !in_calibration_region) {
        // Skip this readout
        continue;
      }

      acq.head.flags.Clear();
      acq.head.scan_counter = scan_counter++;

      if (line == a) {
        acq.head.flags |= static_cast<uint64_t>(AcquisitionFlags::kFirstInEncodeStep1);
        acq.head.flags |= static_cast<uint64_t>(AcquisitionFlags::kFirstInSlice);
        acq.head.flags |= static_cast<uint64_t>(AcquisitionFlags::kFirstInRepetition);
      } else if (line >= nky - acc_factor) {
        acq.head.flags |= static_cast<uint64_t>(AcquisitionFlags::kLastInEncodeStep1);
        acq.head.flags |= static_cast<uint64_t>(AcquisitionFlags::kLastInSlice);
        acq.head.flags |= static_cast<uint64_t>(AcquisitionFlags::kLastInRepetition);
      } else if (in_calibration_region) {
        if (!is_sampled_line) {
          acq.head.flags |= static_cast<uint64_t>(AcquisitionFlags::kIsParallelCalibration);
        } else {
          acq.head.flags |= static_cast<uint64_t>(AcquisitionFlags::kIsParallelCalibrationAndImaging);
        }
      }

      acq.head.idx.kspace_encode_step_1 = line;
      acq.head.idx.slice = 0;
      acq.head.idx.repetition = r;
      acq.data = xt::view(kspace, xt::all(), 0, line, xt::all());

      // Optionally store trajectory coordinates
      if (store_coordinates) {
        acq.trajectory.resize({2, nkx});
        float ky = (1.0f * line - (nky / 2)) / (1.0f * nky);
        for (size_t x = 0; x < nkx; x++) {
          float kx = (1.0f * x - (nkx / 2)) / (1.0f * nkx);
          acq.trajectory(0, x) = kx;
          acq.trajectory(1, x) = ky;
        }
      }

      w->WriteData(acq);
    }
  }
  w->EndData();
  w->Close();
}

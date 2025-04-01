#include "mrd/binary/protocols.h"
#include "mrd/protocols.h"
#include "mrd/types.h"

#include <xtensor-fftw/basic.hpp>
#include <xtensor-fftw/helper.hpp>
#include <xtensor/xstrided_view.hpp>
#include <xtensor/xview.hpp>

xt::xtensor<std::complex<float>, 4> fftshift(xt::xtensor<std::complex<float>, 4> x) {
  return xt::roll(xt::roll(x, x.shape(3) / 2, 3), x.shape(2) / 2, 2);
}

void remove_oversampling(mrd::Acquisition& acq, const mrd::EncodingType& enc) {
  auto new_shape = acq.data.shape();

  auto eNx = enc.encoded_space.matrix_size.x;
  auto rNx = enc.recon_space.matrix_size.x;
  new_shape[1] = rNx;
  auto x_pad = (eNx - rNx) / 2;
  xt::xtensor<std::complex<float>, 2> new_data = xt::zeros<std::complex<float>>(new_shape);
  for (size_t c = 0; c < acq.Coils(); c++) {
    auto ft_line = xt::xarray<std::complex<float>>(xt::view(acq.data, c, xt::all()));
    ft_line = xt::fftw::fftshift(xt::fftw::ifft(xt::fftw::ifftshift(ft_line)));
    ft_line *= std::sqrt(1.0f * ft_line.size());
    ft_line = xt::view(ft_line, xt::range(x_pad, rNx + x_pad));
    ft_line = xt::fftw::fftshift(xt::fftw::fft(xt::fftw::ifftshift(ft_line)));
    ft_line /= std::sqrt(1.0f * ft_line.size());
    xt::view(new_data, c, xt::all()) = ft_line;
  }
  acq.data = new_data;
}

void print_usage(std::string program_name) {
  std::cerr << "Usage: " << program_name << std::endl;
  std::cerr << "  -i|--input   <input MRD stream> (default: stdin)" << std::endl;
  std::cerr << "  -o|--output  <output MRD stream> (default: stdout)" << std::endl;
  std::cerr << "  -h|--help" << std::endl;
}

int main(int argc, char** argv) {
  std::string input_path;
  std::string output_path;

  std::vector<std::string> args(argv, argv + argc);
  auto current_arg = args.begin() + 1;
  while (current_arg != args.end()) {
    if (*current_arg == "--help" || *current_arg == "-h") {
      print_usage(args[0]);
      return 0;
    } else if (*current_arg == "--input" || *current_arg == "-i") {
      current_arg++;
      if (current_arg == args.end()) {
        std::cerr << "Missing input file" << std::endl;
        print_usage(args[0]);
        return 1;
      }
      input_path = *current_arg;
      current_arg++;
    } else if (*current_arg == "--output" || *current_arg == "-o") {
      current_arg++;
      if (current_arg == args.end()) {
        std::cerr << "Missing output file" << std::endl;
        print_usage(args[0]);
        return 1;
      }
      output_path = *current_arg;
      current_arg++;
    } else {
      std::cerr << "Unknown argument: " << *current_arg << std::endl;
      print_usage(args[0]);
      return 1;
    }
  }

  std::unique_ptr<std::ifstream> input_file;
  if (!input_path.empty()) {
    input_file = std::make_unique<std::ifstream>(input_path, std::ios::binary | std::ios::in);
    if (!input_file->good()) {
      throw std::runtime_error("Failed to open input file for reading.");
    }
  }

  std::unique_ptr<std::ofstream> output_file;
  if (!output_path.empty()) {
    output_file = std::make_unique<std::ofstream>(output_path, std::ios::binary | std::ios::out);
    if (!output_file->good()) {
      throw std::runtime_error("Failed to open output file for writing.");
    }
  }

  mrd::binary::MrdReader r(input_path.empty() ? std::cin : *input_file);
  mrd::binary::MrdWriter w(output_path.empty() ? std::cout : *output_file);

  std::optional<mrd::Header> ho;
  r.ReadHeader(ho);
  if (!ho) {
    std::cerr << "Failed to read header" << std::endl;
    return 1;
  }

  auto h = ho.value();
  // Just copy the header
  w.WriteHeader(h);

  auto enc = h.encoding[0];

  auto eNx = enc.encoded_space.matrix_size.x;
  auto eNy = enc.encoded_space.matrix_size.y;
  auto eNz = enc.encoded_space.matrix_size.z;
  auto rNx = enc.recon_space.matrix_size.x;
  auto rNy = enc.recon_space.matrix_size.y;
  auto rNz = enc.recon_space.matrix_size.z;
  auto rFOVx = enc.recon_space.field_of_view_mm.x;
  auto rFOVy = enc.recon_space.field_of_view_mm.y;
  auto rFOVz = enc.recon_space.field_of_view_mm.z;
  if (rFOVz == 0) {
    rFOVz = 1;
  }

  uint32_t ncoils = 1;
  if (h.acquisition_system_information && h.acquisition_system_information->receiver_channels) {
    ncoils = h.acquisition_system_information->receiver_channels.value();
  }

  uint32_t nslices = 1;
  if (enc.encoding_limits.slice.has_value()) {
    nslices = enc.encoding_limits.slice->maximum + 1;
  }

  uint32_t ncontrasts = 1;
  if (enc.encoding_limits.contrast.has_value()) {
    ncontrasts = enc.encoding_limits.contrast->maximum + 1;
  }

  uint32_t ky_offset = 0;
  if (enc.encoding_limits.kspace_encoding_step_1.has_value()) {
    ky_offset = ((eNy + 1) / 2) - enc.encoding_limits.kspace_encoding_step_1->center;
  }

  // When we have aliased types, we will use that.
  mrd::StreamItem v;
  xt::xtensor<std::complex<float>, 6> buffer;
  mrd::Acquisition ref_acq;
  uint32_t image_index = 0;
  while (r.ReadData(v)) {
    if (!std::holds_alternative<mrd::Acquisition>(v)) {
      continue;
    }
    auto acq = std::get<mrd::Acquisition>(v);

    // Currently ignoring noise scans
    if (acq.head.flags.HasFlags(mrd::AcquisitionFlags::kIsNoiseMeasurement)) {
      continue;
    }

    // Remove oversampling
    if (eNx != rNx && acq.Samples() == eNx) {
      remove_oversampling(acq, enc);
    }

    // If this is the first line, we need to allocate the buffer
    if (acq.head.flags.HasFlags(mrd::AcquisitionFlags::kFirstInEncodeStep1) || acq.head.flags.HasFlags(mrd::AcquisitionFlags::kFirstInSlice)) {
      uint32_t readout_length = acq.Samples();
      std::array<size_t, 6> shape = {ncontrasts, nslices, ncoils, eNz, eNy, readout_length};
      buffer = xt::zeros<std::complex<float>>(shape);
      ref_acq = acq;
    }

    // Copy the data into the buffer
    auto contrast = acq.head.idx.contrast.value_or(0);
    auto slice = acq.head.idx.slice.value_or(0);
    auto k1 = acq.head.idx.kspace_encode_step_1.value_or(0);
    auto k2 = acq.head.idx.kspace_encode_step_2.value_or(0);
    xt::view(buffer, contrast, slice, xt::all(), k2, k1 + ky_offset, xt::all()) = xt::xarray<std::complex<float>>(acq.data);

    // If this is the last line, we need to write the buffer
    if (acq.head.flags.HasFlags(mrd::AcquisitionFlags::kLastInEncodeStep1) || acq.head.flags.HasFlags(mrd::AcquisitionFlags::kLastInSlice)) {
      for (unsigned int c = 0; c < buffer.shape(0); c++) {
        for (unsigned int s = 0; s < buffer.shape(1); s++) {
          auto slice = xt::view(buffer, c, s, xt::all(), xt::all(), xt::all(), xt::all());
          slice = fftshift(slice);
          for (unsigned int coil = 0; coil < slice.shape(0); coil++) {
            auto tmp1 = xt::fftw::ifft2(xt::xarray<std::complex<float>>(xt::view(slice, coil, 0, xt::all(), xt::all())));
            tmp1 *= std::sqrt(1.0f * tmp1.size());
            xt::view(slice, coil, 0, xt::all(), xt::all()) = tmp1;
          }
          slice = fftshift(slice);

          std::array<size_t, 4> image_shape = {1, slice.shape(1), slice.shape(2), slice.shape(3)};
          auto pixel_data = xt::sqrt(xt::abs(xt::sum(slice * xt::conj(slice), 0)));

          auto xoffset = (slice.shape(3) + 1) / 2 - (rNx + 1) / 2;
          auto yoffset = (slice.shape(2) + 1) / 2 - (rNy + 1) / 2;
          auto zoffset = (slice.shape(1) + 1) / 2 - (rNz + 1) / 2;
          auto combined = xt::view(pixel_data,
                                   xt::range(zoffset, zoffset + rNz),
                                   xt::range(yoffset, yoffset + rNy),
                                   xt::range(xoffset, xoffset + rNx));

          mrd::Image<float> im;
          im.data = xt::zeros<float>(image_shape);
          xt::view(im.data, 0, xt::all(), xt::all(), xt::all()) = combined;

          im.head.measurement_uid = acq.head.measurement_uid;
          im.head.field_of_view[0] = rFOVx;
          im.head.field_of_view[1] = rFOVy;
          im.head.field_of_view[2] = rFOVz;
          im.head.position = ref_acq.head.position;
          im.head.col_dir = ref_acq.head.read_dir;
          im.head.line_dir = ref_acq.head.phase_dir;
          im.head.slice_dir = ref_acq.head.slice_dir;
          im.head.patient_table_position = ref_acq.head.patient_table_position;
          im.head.average = ref_acq.head.idx.average;
          im.head.slice = ref_acq.head.idx.slice;
          im.head.contrast = ref_acq.head.idx.contrast;
          im.head.phase = ref_acq.head.idx.phase;
          im.head.repetition = ref_acq.head.idx.repetition;
          im.head.set = ref_acq.head.idx.set;
          im.head.acquisition_time_stamp_ns = ref_acq.head.acquisition_time_stamp_ns;
          im.head.physiology_time_stamp_ns = ref_acq.head.physiology_time_stamp_ns;
          im.head.image_type = mrd::ImageType::kMagnitude;
          im.head.image_index = image_index++;
          im.head.image_series_index = 0;
          im.head.user_int = ref_acq.head.user_int;
          im.head.user_float = ref_acq.head.user_float;
          w.WriteData(im);
        }
      }
    }
  }

  w.EndData();

  return 0;
}

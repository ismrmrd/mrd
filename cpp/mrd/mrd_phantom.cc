#include <filesystem>
#include <iostream>

#include "generated/binary/protocols.h"
#include "generated/hdf5/protocols.h"
#include "generated/protocols.h"
#include "generated/types.h"
#include "shepp_logan_phantom.h"
#include <random>
#include <xtensor-fftw/basic.hpp>
#include <xtensor-fftw/helper.hpp>
#include <xtensor/xio.hpp>
#include <xtensor/xview.hpp>

using namespace mrd;

xt::xtensor<std::complex<float>, 4> fftshift(xt::xtensor<std::complex<float>, 4> x)
{
  return xt::roll(xt::roll(x, x.shape(3) / 2, 3), x.shape(2) / 2, 2);
}

xt::xtensor<std::complex<float>, 4> generate_noise(std::array<size_t, 4> shape, float sigma, float mean = 0.0)
{
  xt::xtensor<std::complex<float>, 4> noise = xt::zeros<std::complex<float>>(shape);
  std::random_device rd{};
  std::mt19937 gen;
  gen.seed(rd());
  std::normal_distribution<> d{mean, sigma};
  std::generate(noise.begin(), noise.end(), [&d, &gen]()
                { return std::complex<float>(d(gen), d(gen)); });
  return noise;
}

// This is a quick and dirty implementation. Unnecessary copies, etc.
mrd::ImageData<std::complex<float>> generate_coil_kspace(size_t matrix, size_t ncoils, bool zero_pad = true)
{
  xt::xtensor<std::complex<float>, 4> phan = shepp_logan_phantom(matrix);
  xt::xtensor<std::complex<float>, 4> coils = generate_birdcage_sensitivities(matrix, ncoils, 1.5);
  coils = phan * coils;
  if (zero_pad)
  {
    std::array<size_t, 4> padded_shape = coils.shape();
    padded_shape[3] *= 2;
    xt::xtensor<std::complex<float>, 4> padded = xt::zeros<std::complex<float>>(padded_shape);
    xt::view(padded, xt::all(), xt::all(), xt::all(), xt::range(matrix / 2, matrix / 2 + matrix)) = coils;
    coils = padded;
  }
  coils = fftshift(coils);
  for (unsigned int c = 0; c < ncoils; c++)
  {
    auto tmp1 = xt::fftw::fft2(xt::xarray<std::complex<float>>(xt::view(coils, c, 0, xt::all(), xt::all())));
    tmp1 /= std::sqrt(1.0f * tmp1.size());
    xt::view(coils, c, 0, xt::all(), xt::all()) = tmp1;
  }
  return fftshift(coils);
}

void print_usage(std::string program_name)
{
  std::cerr << "Usage: " << program_name << std::endl;
  std::cerr << "  -o|--output-file <output file>" << std::endl;
  std::cerr << "  -c|--coils       <number of coils>" << std::endl;
  std::cerr << "  -m|--matrix      <matrix size>" << std::endl;
  std::cerr << "  -r|--repetitions <number of repetitions>" << std::endl;
  std::cerr << "  -s|--stdout" << std::endl;
  std::cerr << "  -h|--help" << std::endl;
}

int main(int argc, char **argv)
{
  uint32_t matrix = 256;
  uint32_t ncoils = 8;
  uint32_t repetitions = 1;
  float noise_sigma = 0.05;
  std::string filename = "mrd_testdata.h5";
  bool use_stdout = false;

  std::vector<std::string> args(argv, argv + argc);
  auto current_arg = args.begin() + 1;
  while (current_arg != args.end())
  {
    if (*current_arg == "--help" || *current_arg == "-h")
    {
      print_usage(args[0]);
      return 0;
    }
    else if (*current_arg == "--output-file" || *current_arg == "-o")
    {
      current_arg++;
      if (current_arg == args.end())
      {
        std::cerr << "Missing output file" << std::endl;
        print_usage(args[0]);
        return 1;
      }
      filename = *current_arg;
      current_arg++;
    }
    else if (*current_arg == "--coils" || *current_arg == "-c")
    {
      current_arg++;
      if (current_arg == args.end())
      {
        std::cerr << "Missing number of coils" << std::endl;
        print_usage(args[0]);
        return 1;
      }
      ncoils = std::stoi(*current_arg);
      current_arg++;
    }
    else if (*current_arg == "--matrix" || *current_arg == "-m")
    {
      current_arg++;
      if (current_arg == args.end())
      {
        std::cerr << "Missing matrix size" << std::endl;
        print_usage(args[0]);
        return 1;
      }
      matrix = std::stoi(*current_arg);
      current_arg++;
    }
    else if (*current_arg == "--repetitions" || *current_arg == "-r")
    {
      current_arg++;
      if (current_arg == args.end())
      {
        std::cerr << "Missing number of frames" << std::endl;
        print_usage(args[0]);
        return 1;
      }
      repetitions = std::stoi(*current_arg);
      current_arg++;
    }
    else if (*current_arg == "--noise-sigma" || *current_arg == "-n")
    {
      current_arg++;
      if (current_arg == args.end())
      {
        std::cerr << "Missing noise sigma" << std::endl;
        print_usage(args[0]);
        return 1;
      }
      noise_sigma = std::stof(*current_arg);
      current_arg++;
    }
    else if (*current_arg == "--stdout" || *current_arg == "-s")
    {
      use_stdout = true;
      current_arg++;
    }
    else
    {
      std::cerr << "Unknown argument: " << *current_arg << std::endl;
      print_usage(args[0]);
      return 1;
    }
  }

  // Parameters
  float fov = 300;
  float slice_thickness = 5;

  std::remove(filename.c_str());
  std::unique_ptr<MrdWriterBase> w;

  if (use_stdout)
  {
    w = std::make_unique<mrd::binary::MrdWriter>(std::cout);
  }
  else
  {
    w = std::make_unique<mrd::hdf5::MrdWriter>(filename);
  }

  Header h;
  SubjectInformationType subject;
  subject.patient_id = "1234BGVF";
  subject.patient_name = "John Doe";

  EncodingSpaceType e;
  e.matrix_size = {2 * matrix, matrix, 1};
  e.field_of_view_mm = {2 * fov, fov, slice_thickness};

  EncodingSpaceType r;
  r.matrix_size = {matrix, matrix, 1};
  r.field_of_view_mm = {fov, fov, slice_thickness};

  EncodingType enc;
  enc.trajectory = Trajectory::kCartesian;
  enc.encoded_space = e;
  enc.recon_space = r;
  h.encoding.push_back(enc);

  w->WriteHeader(h);

  // phantom k-space
  auto phan = generate_coil_kspace(matrix, ncoils);

  for (unsigned int r = 0; r < repetitions; r++)
  {
    auto noise = generate_noise(phan.shape(), noise_sigma);
    auto kspace = xt::xtensor<std::complex<float>, 4>(phan) + noise;
    for (size_t line = 0; line < matrix; line++)
    {
      Acquisition a;
      if (line == 0)
      {
        a.flags |= static_cast<uint64_t>(AcquisitionFlags::kFirstInEncodeStep1);
      }
      if (line == matrix - 1)
      {
        a.flags |= static_cast<uint64_t>(AcquisitionFlags::kLastInEncodeStep1);
      }
      a.idx.kspace_encode_step_1 = line;
      a.idx.kspace_encode_step_2 = 0;
      a.idx.slice = 0;
      a.idx.repetition = r;
      a.data = xt::view(kspace, xt::all(), 0, line, xt::all());
      w->WriteData(a);
    }
  }
  w->EndData();
}

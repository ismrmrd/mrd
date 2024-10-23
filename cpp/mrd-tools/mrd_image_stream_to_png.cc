#include "mrd/binary/protocols.h"
#include <Magick++.h>
#include <fmt/format.h>
#include <iostream>

void print_usage(std::string program_name) {
  std::cerr << "Usage: " << program_name << std::endl;
  std::cerr << "  -i|--input          <input MRD stream> (default: stdin)" << std::endl;
  std::cerr << "  -o|--output-prefix  <output file prefix>   (default: image_)" << std::endl;
  std::cerr << "  -h|--help" << std::endl;
}

// Read a stream of MRD images and write them out at PNG files.
int main(int argc, char** argv) {
  std::string input_path;
  std::string prefix = "image_";

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
    } else if (*current_arg == "--output-prefix" || *current_arg == "-o") {
      current_arg++;
      if (current_arg == args.end()) {
        std::cerr << "Missing output file" << std::endl;
        print_usage(args[0]);
        return 1;
      }
      prefix = *current_arg;
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

  mrd::binary::MrdReader r(input_path.empty() ? std::cin : *input_file);

  std::optional<mrd::Header> h;
  r.ReadHeader(h);

  mrd::StreamItem v;
  int image_count = 0;
  while (r.ReadData(v)) {
    if (!std::holds_alternative<mrd::Image<float>>(v)) {
      std::cerr << "Stream must contain only floating point images" << std::endl;
      return 1;
    }

    auto& img = std::get<mrd::Image<float>>(v);

    // Scale image
    // TODO: This segfaults when compiled with C++20
    auto max_value = xt::amax(img.data)();
    img.data *= 1.0 / max_value;

    Magick::Image image(img.Cols(), img.Rows(), "I", Magick::FloatPixel, img.data.data());
    image.depth(8);
    image.type(Magick::GrayscaleType);

    // Use fmt to generate filename from prefix and increment with 6 digits (e.g. prefix_000001.png)
    std::string filename = fmt::format("{}{:06d}.png", prefix, image_count++);
    image.write(filename);
  }

  return 0;
}

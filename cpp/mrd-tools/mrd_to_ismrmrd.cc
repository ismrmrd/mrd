#include "converters.h"
#include "mrd/binary/protocols.h"
#include <exception>
#include <iostream>
#include <ismrmrd/dataset.h>
#include <ismrmrd/meta.h>
#include <ismrmrd/serialization_iostream.h>
#include <ismrmrd/version.h>

#include <date/date.h>

void print_usage(std::string program_name) {
  std::cerr << "Usage: " << program_name << std::endl;
  std::cerr << "  -i|--input   <input MRD stream> (default: stdin)" << std::endl;
  std::cerr << "  -o|--output  <output ISMRMRD stream> (default: stdout)" << std::endl;
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

  ISMRMRD::OStreamView ws(output_path.empty() ? std::cout : *output_file);
  ISMRMRD::ProtocolSerializer serializer(ws);
  mrd::binary::MrdReader r(input_path.empty() ? std::cin : *input_file);

  using namespace mrd::converters;

  std::optional<mrd::Header> header;
  r.ReadHeader(header);
  if (header) {
    serializer.serialize(convert(*header));
  }

  mrd::StreamItem item;
  while (r.ReadData(item)) {
    std::visit([&serializer](auto&& arg) { serializer.serialize(convert(arg)); },
               item);
  }

  serializer.close();

  return 0;
}

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
  std::cerr << "  -i|--input   <input ISMRMRD stream> (default: stdin)" << std::endl;
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

  ISMRMRD::IStreamView rs(input_path.empty() ? std::cin : *input_file);
  ISMRMRD::ProtocolDeserializer deserializer(rs);
  mrd::binary::MrdWriter w(output_path.empty() ? std::cout : *output_file);

  using namespace mrd::converters;

  // Some reconstructions return the header but it is not required.
  if (deserializer.peek() == ISMRMRD::ISMRMRD_MESSAGE_HEADER) {
    ISMRMRD::IsmrmrdHeader hdr;
    deserializer.deserialize(hdr);
    w.WriteHeader(convert(hdr));
  } else {
    w.WriteHeader(std::nullopt);
  }

  while (deserializer.peek() != ISMRMRD::ISMRMRD_MESSAGE_CLOSE) {
    if (deserializer.peek() == ISMRMRD::ISMRMRD_MESSAGE_ACQUISITION) {
      ISMRMRD::Acquisition acq;
      deserializer.deserialize(acq);
      w.WriteData(convert(acq));
    } else if (deserializer.peek() == ISMRMRD::ISMRMRD_MESSAGE_IMAGE) {
      if (deserializer.peek_image_data_type() == ISMRMRD::ISMRMRD_USHORT) {
        ISMRMRD::Image<unsigned short> img;
        deserializer.deserialize(img);
        w.WriteData(convert(img));
      } else if (deserializer.peek_image_data_type() == ISMRMRD::ISMRMRD_SHORT) {
        ISMRMRD::Image<short> img;
        deserializer.deserialize(img);
        w.WriteData(convert(img));
      } else if (deserializer.peek_image_data_type() == ISMRMRD::ISMRMRD_UINT) {
        ISMRMRD::Image<unsigned int> img;
        deserializer.deserialize(img);
        w.WriteData(convert(img));
      } else if (deserializer.peek_image_data_type() == ISMRMRD::ISMRMRD_INT) {
        ISMRMRD::Image<int> img;
        deserializer.deserialize(img);
        w.WriteData(convert(img));
      } else if (deserializer.peek_image_data_type() == ISMRMRD::ISMRMRD_FLOAT) {
        ISMRMRD::Image<float> img;
        deserializer.deserialize(img);
        w.WriteData(convert(img));
      } else if (deserializer.peek_image_data_type() == ISMRMRD::ISMRMRD_DOUBLE) {
        ISMRMRD::Image<double> img;
        deserializer.deserialize(img);
        w.WriteData(convert(img));
      } else if (deserializer.peek_image_data_type() == ISMRMRD::ISMRMRD_CXFLOAT) {
        ISMRMRD::Image<std::complex<float>> img;
        deserializer.deserialize(img);
        w.WriteData(convert(img));
      } else if (deserializer.peek_image_data_type() == ISMRMRD::ISMRMRD_CXDOUBLE) {
        ISMRMRD::Image<std::complex<double>> img;
        deserializer.deserialize(img);
        w.WriteData(convert(img));
      } else {
        throw std::runtime_error("Unknown image type");
      }
    } else if (deserializer.peek() == ISMRMRD::ISMRMRD_MESSAGE_WAVEFORM) {
      ISMRMRD::Waveform wfm;
      deserializer.deserialize(wfm);
      w.WriteData(convert(wfm));
    } else {
      std::cerr << "Unexpected ISMRMRD message type: " << deserializer.peek() << std::endl;
      return 1;
    }
  }

  w.EndData();

  return 0;
}

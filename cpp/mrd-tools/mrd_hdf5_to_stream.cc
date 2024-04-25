#include "mrd/binary/protocols.h"
#include "mrd/hdf5/protocols.h"
#include <filesystem>
#include <iostream>

int main(int argc, char **argv)
{
  if (argc < 2)
  {
    std::cerr << "Usage: " << argv[0] << " <filename>" << std::endl;
    return 1;
  }

  std::string filename = argv[1];

  mrd::hdf5::MrdReader r(filename);
  mrd::binary::MrdWriter w(std::cout);
  r.CopyTo(w);
  return 0;
}

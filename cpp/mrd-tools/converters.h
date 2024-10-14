#pragma once

#include "mrd/types.h"

#include <ismrmrd/xml.h>
#include <ismrmrd/waveform.h>

namespace mrd::converters {

ISMRMRD::IsmrmrdHeader convert(Header& hdr);
ISMRMRD::Acquisition convert(Acquisition& acq);
ISMRMRD::Waveform convert(Waveform<uint32_t>& wfm);
ISMRMRD::Image<unsigned short> convert(Image<unsigned short>& im);
ISMRMRD::Image<short> convert(Image<short>& im);
ISMRMRD::Image<unsigned int> convert(Image<unsigned int>& im);
ISMRMRD::Image<int> convert(Image<int>& im);
ISMRMRD::Image<float> convert(Image<float>& im);
ISMRMRD::Image<double> convert(Image<double>& im);
ISMRMRD::Image<std::complex<float>> convert(Image<std::complex<float>>& im);
ISMRMRD::Image<std::complex<double>> convert(Image<std::complex<double>>& im);
int convert(AcquisitionBucket&);
int convert(ReconData&);
int convert(ImageArray&);
int convert(ArrayComplexFloat&);

Header convert(ISMRMRD::IsmrmrdHeader& hdr);
Acquisition convert(ISMRMRD::Acquisition& acq);
Waveform<uint32_t> convert(ISMRMRD::Waveform& wfm);
Image<unsigned short> convert(ISMRMRD::Image<unsigned short>& im);
Image<short> convert(ISMRMRD::Image<short>& im);
Image<unsigned int> convert(ISMRMRD::Image<unsigned int>& im);
Image<int> convert(ISMRMRD::Image<int>& im);
Image<float> convert(ISMRMRD::Image<float>& im);
Image<double> convert(ISMRMRD::Image<double>& im);
Image<std::complex<float>> convert(ISMRMRD::Image<std::complex<float>>& im);
Image<std::complex<double>> convert(ISMRMRD::Image<std::complex<double>>& im);

} // namespace mrd::converters

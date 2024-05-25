#include "shepp_logan_phantom.h"
#include "mrd/types.h"

mrd::ImageData<std::complex<float>> phantom(std::vector<PhantomEllipse> &ellipses, unsigned int matrix_size)
{
  std::array<size_t, 4> shape = {1, 1, matrix_size, matrix_size};
  mrd::ImageData<std::complex<float>> out = xt::zeros<std::complex<float>>(shape);
  for (std::vector<PhantomEllipse>::iterator it = ellipses.begin(); it != ellipses.end(); it++)
  {
    for (unsigned int y = 0; y < matrix_size; y++)
    {
      float y_co = (1.0f * y - (matrix_size >> 1)) / (matrix_size >> 1);
      for (unsigned int x = 0; x < matrix_size; x++)
      {
        float x_co = (1.0f * x - (matrix_size >> 1)) / (matrix_size >> 1);
        if (it->isInside(x_co, y_co))
        {
          out(0, 0, y, x) += std::complex<float>(it->getAmplitude(), 0.0);
        }
      }
    }
  }
  return out;
}

mrd::ImageData<std::complex<float>> shepp_logan_phantom(unsigned int matrix_size)
{
  std::vector<PhantomEllipse> e = modified_shepp_logan_ellipses();
  return phantom(e, matrix_size);
}

std::vector<PhantomEllipse> shepp_logan_ellipses()
{
  std::vector<PhantomEllipse> out;
  out.push_back(PhantomEllipse(1.0f, 0.6900f, 0.9200f, 0.00f, 0.0000f, 0.0f));
  out.push_back(PhantomEllipse(-0.98f, 0.6624f, 0.8740f, 0.00f, -0.0184f, 0.0f));
  out.push_back(PhantomEllipse(-0.02f, 0.1100f, 0.3100f, 0.22f, 0.0000f, -18.0f));
  out.push_back(PhantomEllipse(-0.02f, 0.1600f, 0.4100f, -0.22f, 0.0000f, 18.0f));
  out.push_back(PhantomEllipse(0.01f, 0.2100f, 0.2500f, 0.00f, 0.3500f, 0.0f));
  out.push_back(PhantomEllipse(0.01f, 0.0460f, 0.0460f, 0.00f, 0.1000f, 0.0f));
  out.push_back(PhantomEllipse(0.01f, 0.0460f, 0.0460f, 0.00f, -0.1000f, 0.0f));
  out.push_back(PhantomEllipse(0.01f, 0.0460f, 0.0230f, -0.08f, -0.6050f, 0.0f));
  out.push_back(PhantomEllipse(0.01f, 0.0230f, 0.0230f, 0.00f, -0.6060f, 0.0f));
  out.push_back(PhantomEllipse(0.01f, 0.0230f, 0.0460f, 0.06f, -0.6050f, 0.0f));
  return out;
}

std::vector<PhantomEllipse> modified_shepp_logan_ellipses()
{
  std::vector<PhantomEllipse> out;
  out.push_back(PhantomEllipse(1.0f, .6900f, .9200f, 0.00f, 0.0000f, 0.0f));
  out.push_back(PhantomEllipse(-0.8f, .6624f, .8740f, 0.00f, -0.0184f, 0.0f));
  out.push_back(PhantomEllipse(-0.2f, .1100f, .3100f, 0.22f, 0.0000f, -18.0f));
  out.push_back(PhantomEllipse(-0.2f, .1600f, .4100f, -0.22f, 0.0000f, 18.0f));
  out.push_back(PhantomEllipse(0.1f, .2100f, .2500f, 0.00f, 0.3500f, 0.0f));
  out.push_back(PhantomEllipse(0.1f, .0460f, .0460f, 0.00f, 0.1000f, 0.0f));
  out.push_back(PhantomEllipse(0.1f, .0460f, .0460f, 0.00f, -0.1000f, 0.0f));
  out.push_back(PhantomEllipse(0.1f, .0460f, .0230f, -0.08f, -0.6050f, 0.0f));
  out.push_back(PhantomEllipse(0.1f, .0230f, .0230f, 0.00f, -0.6060f, 0.0f));
  out.push_back(PhantomEllipse(0.1f, .0230f, .0460f, 0.06f, -0.6050f, 0.0f));
  return out;
}

mrd::ImageData<std::complex<float>> generate_birdcage_sensitivities(unsigned int matrix_size, unsigned int ncoils, float relative_radius)
{
  // This function is heavily inspired by the mri_birdcage.m Matlab script in Jeff Fessler's IRT packake
  // http://web.eecs.umich.edu/~fessler/code/
  std::array<size_t, 4> shape = {ncoils, 1, matrix_size, matrix_size};
  mrd::ImageData<std::complex<float>> out = xt::zeros<std::complex<float>>(shape);

  for (unsigned int c = 0; c < ncoils; c++)
  {
    float coilx = relative_radius * std::cos(c * (2 * 3.14159265359f / ncoils));
    float coily = relative_radius * std::sin(c * (2 * 3.14159265359f / ncoils));
    float coil_phase = -1.0f * c * (2 * 3.14159265359f / ncoils);
    for (unsigned int y = 0; y < matrix_size; y++)
    {
      float y_co = (1.0f * y - (matrix_size >> 1)) / (matrix_size >> 1) - coily;
      for (unsigned int x = 0; x < matrix_size; x++)
      {
        float x_co = (1.0f * x - (matrix_size >> 1)) / (matrix_size >> 1) - coilx;
        float rr = std::sqrt(x_co * x_co + y_co * y_co);
        float phi = atan2(x_co, -y_co) + coil_phase;
        out(c, 0, y, x) = std::polar(1 / rr, phi);
      }
    }
  }

  return out;
}

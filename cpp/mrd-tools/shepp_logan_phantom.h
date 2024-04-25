#pragma once

#include "mrd/types.h"
#include <complex>
#include <vector>

class PhantomEllipse
{
public:
  PhantomEllipse(float A, float a, float b, float x0, float y0, float phi)
      : A_(A), a_(a), b_(b), x0_(x0), y0_(y0), phi_(phi)
  {
  }

  bool isInside(float x, float y)
  {
    float asq = a_ * a_;                     // a^2
    float bsq = b_ * b_;                     // b^2
    float phi = phi_ * 3.14159265359f / 180; // rotation angle in radians
    float x0 = x - x0_;                      // x offset
    float y0 = y - y0_;                      // y offset
    float cosp = cos(phi);
    float sinp = sin(phi);
    return (((x0 * cosp + y0 * sinp) * (x0 * cosp + y0 * sinp)) / asq + ((y0 * cosp - x0 * sinp) * (y0 * cosp - x0 * sinp)) / bsq <= 1);
  }

  float getAmplitude()
  {
    return A_;
  }

protected:
  float A_;
  float a_;
  float b_;
  float x0_;
  float y0_;
  float phi_;
};

std::vector<PhantomEllipse> shepp_logan_ellipses();
std::vector<PhantomEllipse> modified_shepp_logan_ellipses();
mrd::ImageData<std::complex<float>> phantom(std::vector<PhantomEllipse> &coefficients, unsigned int matrix_size);
mrd::ImageData<std::complex<float>> shepp_logan_phantom(unsigned int matrix_size);
mrd::ImageData<std::complex<float>> generate_birdcage_sensitivities(unsigned int matrix_size, unsigned int ncoils, float relative_radius);

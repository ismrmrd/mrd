#pragma once

#include <complex>
#include <cstring>
#include <fftw3.h>
#include <xtensor/containers/xarray.hpp>
#include <xtensor/misc/xmanipulation.hpp>

namespace fftw_wrappers {

namespace detail {

// Helper function for 1D FFTW operations
template <class E>
inline auto fftw_1d_impl(E&& e, int direction, bool normalize) -> xt::xarray<std::complex<float>> {
  auto size = e.size();

  std::vector<size_t> shape = {size};
  xt::xarray<std::complex<float>> result = xt::zeros<std::complex<float>>(shape);
  xt::xarray<std::complex<float>> input = e;

  fftwf_complex* in = reinterpret_cast<fftwf_complex*>(input.data());
  fftwf_complex* out = reinterpret_cast<fftwf_complex*>(result.data());

  fftwf_plan plan = fftwf_plan_dft_1d(size, in, out, direction, FFTW_ESTIMATE);
  fftwf_execute(plan);
  fftwf_destroy_plan(plan);

  if (normalize) {
    result /= static_cast<float>(size);
  }

  return result;
}

// Helper function for 2D FFTW operations
template <class E>
inline auto fftw_2d_impl(E&& e, int direction, bool normalize) -> xt::xarray<std::complex<float>> {
  auto shape = e.shape();

  if (shape.size() != 2) {
    throw std::runtime_error(direction == FFTW_FORWARD ? "fft2 requires 2D input" : "ifft2 requires 2D input");
  }

  auto n0 = shape[0];
  auto n1 = shape[1];

  std::vector<size_t> result_shape = {n0, n1};
  xt::xarray<std::complex<float>> result = xt::zeros<std::complex<float>>(result_shape);
  xt::xarray<std::complex<float>> input = e;

  fftwf_complex* in = reinterpret_cast<fftwf_complex*>(input.data());
  fftwf_complex* out = reinterpret_cast<fftwf_complex*>(result.data());

  fftwf_plan plan = fftwf_plan_dft_2d(n0, n1, in, out, direction, FFTW_ESTIMATE);
  fftwf_execute(plan);
  fftwf_destroy_plan(plan);

  if (normalize) {
    result /= static_cast<float>(n0 * n1);
  }

  return result;
}
} // namespace detail

// FFT shift functions
template <class E>
inline auto fftshift(E&& e) -> xt::xarray<typename std::decay_t<E>::value_type> {
  xt::xarray<typename std::decay_t<E>::value_type> result = e;

  for (std::size_t ax = 0; ax < result.dimension(); ++ax) {
    auto size = result.shape()[ax];
    auto shift = size / 2;
    result = xt::roll(result, shift, ax);
  }
  return result;
}

template <class E>
inline auto ifftshift(E&& e) -> xt::xarray<typename std::decay_t<E>::value_type> {
  xt::xarray<typename std::decay_t<E>::value_type> result = e;

  for (std::size_t ax = 0; ax < result.dimension(); ++ax) {
    auto size = result.shape()[ax];
    auto shift = (size + 1) / 2; // Different from fftshift for odd sizes
    result = xt::roll(result, shift, ax);
  }
  return result;
}

// 1D FFT/IFFT wrappers - now using shared implementation
template <class E>
inline auto fft(E&& e) -> xt::xarray<std::complex<float>> {
  return detail::fftw_1d_impl(std::forward<E>(e), FFTW_FORWARD, false);
}

template <class E>
inline auto ifft(E&& e) -> xt::xarray<std::complex<float>> {
  return detail::fftw_1d_impl(std::forward<E>(e), FFTW_BACKWARD, true);
}

// 2D FFT/IFFT wrappers - now using shared implementation
template <class E>
inline auto fft2(E&& e) -> xt::xarray<std::complex<float>> {
  return detail::fftw_2d_impl(std::forward<E>(e), FFTW_FORWARD, false);
}

template <class E>
inline auto ifft2(E&& e) -> xt::xarray<std::complex<float>> {
  return detail::fftw_2d_impl(std::forward<E>(e), FFTW_BACKWARD, true);
}

} // namespace fftw_wrappers

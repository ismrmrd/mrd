#include "generated/binary/protocols.h"
#include <filesystem>
#include <iostream>
#include <Magick++.h>
#include <fmt/format.h>

// Read a stream of MRD images and write them out at PNG files.
int main(int argc, char **argv)
{
    std::string prefix = "image_";
    if (argc > 2)
    {
        std::cerr << "Usage: " << argv[0] << " <prefix>" << std::endl;
        return 1;
    }
    else if (argc == 2)
    {
        prefix = argv[1];
    }

    mrd::binary::MrdReader r(std::cin);

    std::optional<mrd::Header> h;
    r.ReadHeader(h);

    mrd::StreamItem v;
    int image_count = 0;
    while (r.ReadData(v))
    {
        if (!std::holds_alternative<mrd::Image<float>>(v))
        {
            std::cerr << "Stream must contain only floating point images" << std::endl;
            return 1;
        }

        auto &img = std::get<mrd::Image<float>>(v);

        // Scale image
        auto max_value = xt::amax(img.data)();
        img.data *= 1.0 / max_value;

        Magick::Image image(img.Cols(), img.Rows(), "I", Magick::FloatPixel, img.data.data());

        // Use fmt to generate filename from prefix and increment with 6 digits (e.g. prefix_000001.png)
        std::string filename = fmt::format("{}{:06d}.png", prefix, image_count++);
        image.write(filename);
    }

    return 0;
}

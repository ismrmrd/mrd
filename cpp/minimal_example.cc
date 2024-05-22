#include "mrd/binary/protocols.h"

int main(void)
{
    mrd::binary::MrdWriter w("test.bin");

    mrd::Header header;
    // Populate Header
    // ...

    w.WriteHeader(header);

    unsigned int nreps = 2;
    for (unsigned int r = 0; r < nreps; r++)
    {
        mrd::Acquisition acq;
        // Populate Acquisition
        // ...

        w.WriteData(acq);
    }
    w.EndData();
    w.Close();

    mrd::binary::MrdReader r("test.bin");

    std::optional<mrd::Header> header_in;
    r.ReadHeader(header_in);

    mrd::StreamItem v;
    while (r.ReadData(v))
    {
        if (!std::holds_alternative<mrd::Acquisition>(v))
        {
            continue;
        }

        auto acq = std::get<mrd::Acquisition>(v);
        // Process Acquisition
        // ...
    }
    r.Close();

    return 0;
}

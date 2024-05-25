import mrd

# Produce Acquisitions via a Python generator - simulating a stream
def generate_data():
    nreps = 2
    for _ in range(nreps):
        acq = mrd.Acquisition()
        # Populate Acquisition
        # ...
        yield mrd.StreamItem.Acquisition(acq)


header = mrd.Header()
# Populate Header
# ...

with mrd.BinaryMrdWriter("test.bin") as w:
    w.write_header(header)
    w.write_data(generate_data())

with mrd.BinaryMrdReader("test.bin") as r:
    header = r.read_header()
    data_stream = r.read_data()
    for item in data_stream:
        # Process StreamItem (Acquisition, Image, or Waveform)
        # ...
        pass

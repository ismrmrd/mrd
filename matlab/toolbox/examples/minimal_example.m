header = mrd.Header();
% Populate Header
% ...

w = mrd.binary.MrdWriter("test.bin");
w.write_header(header);

nreps = 2;
for r = 1:nreps
    acq = mrd.Acquisition();
    % Populate Acquisition
    % ...

    w.write_data(mrd.StreamItem.Acquisition(acq));
end
w.end_data();
w.close();

r = mrd.binary.MrdReader("test.bin");
header = r.read_header();
while r.has_data()
    item = r.read_data();
    acq = item.value;
end
r.close();

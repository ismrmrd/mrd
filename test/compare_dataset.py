import argparse
import mrd

def read_dataset(filename: str) -> tuple[mrd.Header, list[mrd.Acquisition]]:
    acquisitions = []
    with mrd.BinaryMrdReader(filename) as reader:
        header = reader.read_header()
        if header is None:
            raise RuntimeError(f"No header found in {filename}")
        for item in reader.read_data():
            if isinstance(item, mrd.StreamItem.Acquisition):
                acquisitions.append(item.value)
    return header, acquisitions

def compare_datasets(file_a: str, file_b: str):
    header_a, acquisitions_a = read_dataset(file_a)
    header_b, acquisitions_b = read_dataset(file_b)

    assert header_a == header_b, "Headers do not match"
    assert len(acquisitions_a) == len(acquisitions_b), "Number of acquisitions do not match"

    for i, (acq_a, acq_b) in enumerate(zip(acquisitions_a, acquisitions_b)):
        if acq_a.head != acq_b.head:
            print(acq_a.head.__dict__.items())
            print(acq_b.head.__dict__.items())
        assert acq_a.head == acq_b.head, f"Acquisition {i} headers do not match"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Validate that two MRD Acquisition datasets are equivalent')
    parser.add_argument('a', type=str, help='Test dataset A')
    parser.add_argument('b', type=str, help='Test dataset B')
    args = parser.parse_args()
    compare_datasets(args.a, args.b)

import argparse
import ismrmrd


def compare_streams(deserializer_a: ismrmrd.ProtocolDeserializer, deserializer_b: ismrmrd.ProtocolDeserializer):
    gen_a = deserializer_a.deserialize()
    gen_b = deserializer_b.deserialize()

    for i, (item_a, item_b) in enumerate(zip(gen_a, gen_b)):
        assert type(item_a) == type(item_b), f"Item {i} types do not match: {type(item_a)} != {type(item_b)}"

        # The Image Meta is serialized differently between the C++ and Python ISMRMRD libraries,
        # so we need to "correct" the `attribute_string_len` value on the ImageHeader before comparison
        for item in (item_a, item_b):
            if isinstance(item, ismrmrd.Image):
                head = item.getHead()
                head.attribute_string_len = item.attribute_string_len
                item.setHead(head)

        assert item_a == item_b, f"Item {i} does not match {item_a} != {item_b}"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Validate that two ISMRMRD streams are equivalent')
    parser.add_argument('a', type=str, help='Test stream A')
    parser.add_argument('b', type=str, help='Test stream B')
    args = parser.parse_args()
    with ismrmrd.ProtocolDeserializer(args.a) as deserializer_a:
        with ismrmrd.ProtocolDeserializer(args.b) as deserializer_b:
            compare_streams(deserializer_a, deserializer_b)

#!/usr/bin/env python3
"""Cross-version read test for phantom files.

Reads one or more MRD phantom files (each written by a possibly-different
branch/schema) with the CURRENT library, comparing the stock
``BinaryMrdReader`` against the schema-tolerant ``DynamicMrdReader``.

For each file it reports:
  - whether the embedded schema matches the current compiled-in schema;
  - whether ``BinaryMrdReader`` can open it (it rejects mismatched schemas);
  - whether ``DynamicMrdReader`` can open it and how many of each StreamItem
    variant it decoded, plus any variants present in the file with no current
    model equivalent (surfaced as UnknownUnionCase).

A file written by the *current* branch should read with both. A file written by
a *different* branch (different schema) should be rejected by BinaryMrdReader
but read by DynamicMrdReader.

Usage:
    python3 read_phantom_cross_version.py <file.bin> [<file2.bin> ...]
"""

import sys
from collections import Counter

import mrd
from mrd.dynamic import DynamicMrdReader, UnknownUnionCase


def try_binary_reader(path: str) -> str:
    try:
        with mrd.BinaryMrdReader(path) as r:
            r.read_header()
            n = sum(1 for _ in r.read_data())
        return f"OK ({n} items)"
    except Exception as e:  # noqa: BLE001 - reporting only
        return f"REJECTED ({type(e).__name__}: {e})"


def read_dynamic(path: str) -> tuple[bool, Counter, list, object]:
    counts: Counter = Counter()
    unknown: list[UnknownUnionCase] = []
    with DynamicMrdReader(path) as r:
        matches = r.schema_matches
        header = r.read_header()
        for item in r.read_data():
            counts[type(item).__name__] += 1
            if isinstance(item, UnknownUnionCase):
                unknown.append(item)
        unmatched = list(r.unmatched_variants)
    return matches, counts, unmatched, header


def main(paths: list[str]) -> int:
    failures = 0
    for path in paths:
        print(f"\n=== {path} ===")

        # 1. Stock reader: strict schema check
        print(f"  BinaryMrdReader:   {try_binary_reader(path)}")

        # 2. Dynamic reader: schema-tolerant
        try:
            matches, counts, unmatched, header = read_dynamic(path)
        except Exception as e:  # noqa: BLE001
            print(f"  DynamicMrdReader:  FAILED ({type(e).__name__}: {e})")
            failures += 1
            continue

        total = sum(counts.values())
        print(f"  DynamicMrdReader:  OK ({total} items)")
        print(f"    schema_matches:  {matches}")
        print(f"    header:          {'present' if header is not None else 'None'}")
        for name, n in sorted(counts.items()):
            print(f"      {name}: {n}")
        if unmatched:
            print(f"    unmatched variants (file-only): {unmatched}")

        # Sanity: a phantom must contain at least one acquisition and a header.
        if header is None or counts.get("StreamItem.Acquisition", 0) == 0:
            print("    !! expected a header and >=1 acquisition")
            failures += 1

    print()
    if failures:
        print(f"FAILED: {failures} file(s) did not read as expected.")
        return 1
    print("All phantom files read successfully with DynamicMrdReader.")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1:]))

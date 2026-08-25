from __future__ import annotations

from pathlib import Path

import pytest
from mrd.tools.phantom import generate_cartesian_phantom
from mrd.tools.stream_recon import reconstruct_mrd_stream


@pytest.fixture(scope="session")
def generated_mrd_pair(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, Path]:
    root = tmp_path_factory.mktemp("generated_mrds")
    raw_path = root / "phantom_raw.mrd"
    recon_path = root / "phantom_recon.mrd"

    generate_cartesian_phantom(
        str(raw_path),
        ncoils=4,
        matrix_size=16,
        repetitions=2,
        oversampling=2,
        noise_level=0.0,
    )
    with raw_path.open("rb") as input_stream, recon_path.open("wb") as output_stream:
        reconstruct_mrd_stream(input_stream, output_stream)

    return raw_path, recon_path
import argparse
import sys
from typing import Iterable, Optional, TextIO, Union, Tuple
import numpy as np
import mrd

_PULSEQ_VERSION_1_4_2 = (1, 4, 2)
_PULSEQ_VERSION_1_5_0 = (1, 5, 0)
_PULSEQ_VERSION_1_5_1 = (1, 5, 1)

_PULSEQ_SUPPORTED_VERSIONS = [
    _PULSEQ_VERSION_1_4_2,
    _PULSEQ_VERSION_1_5_0,
    _PULSEQ_VERSION_1_5_1,
]


def _version_to_string(version: Tuple[int, int, int]) -> str:
    return f"{version[0]}.{version[1]}.{version[2]}"


_abbreviation_to_rf_use_dict = {e.name.lower()[0]: e for e in mrd.RFPulseUse}


def _get_rf_use_from_abbreviation(abbreviation: str) -> mrd.RFPulseUse:
    try:
        return _abbreviation_to_rf_use_dict[abbreviation]
    except KeyError:
        raise ValueError(f"Invalid RF use abbreviation '{abbreviation}'") from None


class _LinesIterator:
    """
    Internal implementation of a peekable line iterator for pulseq .seq files.

    Behavior:
      - Strips whitespace.
      - Skips comment lines beginning with '#'.
      - Provides lookahead via peek().
      - Line numbers correspond to the original file (1-based).
    """

    def __init__(self, file: TextIO):
        self._file = file
        self._buffer: Union[Tuple[int, str], None] = None
        self._line_number = 0

    def __iter__(self) -> "_LinesIterator":
        return self

    def __next__(self) -> Tuple[int, str]:
        if self._buffer is not None:
            item = self._buffer
            self._buffer = None
            return item

        while True:
            raw = self._file.readline()
            if raw == "":  # EOF
                raise StopIteration
            self._line_number += 1
            line = raw.strip()
            if line.startswith("#"):
                continue
            return self._line_number, line

    def peek(self) -> Optional[Tuple[int, str]]:
        if self._buffer is not None:
            return self._buffer
        try:
            self._buffer = self.__next__()
        except StopIteration:
            return None
        return self._buffer

    def skip_empty_lines(self) -> None:
        while True:
            next_line = self.peek()
            if next_line is None or next_line[1] != "":
                break
            next(self)

    def read_until_next_section(self) -> Iterable[Tuple[int, str]]:
        while True:
            next_line = self.peek()
            if next_line is None or (
                next_line[1].startswith("[") and next_line[1].endswith("]")
            ):
                break

            yield next(self)


def pulseq_text_to_stream_items(file: TextIO) -> Iterable[mrd.StreamItem]:
    linesIterable = _LinesIterator(file)

    linesIterable.skip_empty_lines()
    line_number, line = next(linesIterable)
    if line != "[VERSION]":
        raise RuntimeError(
            f"Line {line_number}: Expected [VERSION] section start, got '{line}'"
        )

    version = _parse_version(linesIterable)
    if version not in _PULSEQ_SUPPORTED_VERSIONS:
        raise RuntimeError(
            f"Unsupported pulseq version {_version_to_string(version)}. "
            + f"Supported versions are: {', '.join(_version_to_string(v) for v in _PULSEQ_SUPPORTED_VERSIONS)}"
        )

    definitions: Optional[mrd.PulseqDefinitions] = None
    blocks: list[mrd.Block] = []
    rf_events: list[mrd.RFEvent] = []
    trapezoidal_gradients: list[mrd.TrapezoidalGradient] = []
    arbitrary_gradients: list[mrd.ArbitraryGradient] = []
    adc_events: list[mrd.ADCEvent] = []
    shapes: list[mrd.Shape] = []

    for line_number, line in linesIterable:
        if line == "":
            continue
        elif line == "[DEFINITIONS]":
            if version is None:
                raise RuntimeError(
                    f"Line {line_number}: [DEFINITIONS] section before [VERSION] section"
                )
            definitions = _parse_definitions(linesIterable)
        elif line == "[BLOCKS]":
            blocks = _parse_blocks(linesIterable)
        elif line == "[RF]":
            rf_events = _parse_rf_events(linesIterable, version)
        elif line == "[TRAP]":
            trapezoidal_gradients = _parse_trap_gradients(linesIterable)
        elif line == "[GRADIENTS]":
            arbitrary_gradients = _parse_arbitrary_gradients(linesIterable, version)
        elif line == "[ADC]":
            adc_events = _parse_adc_events(linesIterable, version)
        elif line == "[SHAPES]":
            shapes = _parse_shapes(linesIterable)
        elif line == "[SIGNATURE]":
            _parse_signature(linesIterable)
        else:
            if line.startswith("[") and line.endswith("]"):
                raise RuntimeError(
                    f"Line {line_number}: Unexpected section start `{line}`"
                )

            raise RuntimeError(f"Line {line_number}: unexpected line `{line}`")

    if definitions:
        yield mrd.StreamItem.PulseqDefinitions(definitions)
    for shape in shapes:
        yield mrd.StreamItem.Shape(shape)
    for rf in rf_events:
        yield mrd.StreamItem.Rf(rf)
    for trap in trapezoidal_gradients:
        yield mrd.StreamItem.TrapezoidalGradient(trap)
    for grad in arbitrary_gradients:
        yield mrd.StreamItem.ArbitraryGradient(grad)
    for adc in adc_events:
        yield mrd.StreamItem.Adc(adc)
    yield mrd.StreamItem.Blocks(blocks)


def _parse_version(lines: _LinesIterator) -> Tuple[int, int, int]:
    major, minor, revision = (0, 0, 0)
    for line_number, line in lines.read_until_next_section():
        if line == "":
            break
        try:
            tokens = line.split()
            if len(tokens) != 2:
                raise RuntimeError(f"Line {line_number}: Invalid version {line}")
            key, value = tokens
            if key == "major":
                major = int(value)
            elif key == "minor":
                minor = int(value)
            elif key == "revision":
                revision = int(value)
            else:
                raise RuntimeError(f"Invalid version key {key}")
        except Exception as e:
            raise RuntimeError(
                f"Line {line_number}: Invalid version line {line}"
            ) from e

    return major, minor, revision


def _parse_definitions(lines: _LinesIterator) -> mrd.PulseqDefinitions:
    definitions = mrd.PulseqDefinitions()
    for line_number, line in lines.read_until_next_section():
        if line == "":
            continue
        try:
            tokens = line.split(" ")
            key, *values = tokens
            if key == "GradientRasterTime":
                definitions.gradient_raster_time = float(values[0])
            elif key == "RadiofrequencyRasterTime":
                definitions.radiofrequency_raster_time = float(values[0])
            elif key == "AdcRasterTime":
                definitions.adc_raster_time = float(values[0])
            elif key == "BlockDurationRaster":
                definitions.block_duration_raster = float(values[0])
            elif key == "Name":
                definitions.name = values[0]
            elif key == "FOV":
                if len(values) != 3:
                    raise RuntimeError(f"Invalid FOV `{line}`")
                definitions.fov = mrd.ThreeDimensionalFloat(
                    x=float(values[0]), y=float(values[1]), z=float(values[2])
                )
            elif key == "TotalDuration":
                definitions.total_duration = float(values[0])
            else:
                definitions.custom[key] = " ".join(values)
        except Exception as e:
            raise RuntimeError(
                f"Line {line_number}: Invalid definition `{line}`"
            ) from e

    return definitions


def _parse_blocks(lines: _LinesIterator) -> list[mrd.Block]:
    blocks: list[mrd.Block] = []
    for line_number, line in lines.read_until_next_section():
        if line == "":
            continue
        tokens = line.split()
        try:
            if len(tokens) != 8:
                raise RuntimeError(f"Line {line_number}: Invalid block `{line}`")

            block = mrd.Block(
                id=int(tokens[0]),
                duration=int(tokens[1]),
                rf=int(tokens[2]),
                gx=int(tokens[3]),
                gy=int(tokens[4]),
                gz=int(tokens[5]),
                adc=int(tokens[6]),
                ext=int(tokens[7]),
            )
        except Exception as e:
            raise RuntimeError(f"Line {line_number}: Invalid block `{line}`") from e

        blocks.append(block)

    return blocks


def _parse_rf_events(lines: _LinesIterator, version) -> list[mrd.RFEvent]:
    rf_events: list[mrd.RFEvent] = []
    for line_number, line in lines.read_until_next_section():
        if line == "":
            continue
        tokens = line.split()
        try:
            if version >= _PULSEQ_VERSION_1_5_0:
                if len(tokens) != 12:
                    raise RuntimeError(
                        f"Line {line_number}: Invalid RF event `{line}`"
                    )

                rf_event = mrd.RFEvent(
                    id=int(tokens[0]),
                    amp=float(tokens[1]),
                    mag_id=int(tokens[2]),
                    phase_id=int(tokens[3]),
                    time_id=int(tokens[4]),
                    center=int(tokens[5]),
                    delay=int(tokens[6]),
                    freq_ppm=float(tokens[7]),
                    phase_ppm=float(tokens[8]),
                    freq_offset=float(tokens[9]),
                    phase_offset=float(tokens[10]),
                    use=_get_rf_use_from_abbreviation(tokens[11]),
                )
            else:
                if len(tokens) != 8:
                    raise RuntimeError(
                        f"Line {line_number}: Invalid RF event `{line}`"
                    )
                rf_event = mrd.RFEvent(
                    id=int(tokens[0]),
                    amp=float(tokens[1]),
                    mag_id=int(tokens[2]),
                    phase_id=int(tokens[3]),
                    time_id=int(tokens[4]),
                    delay=int(tokens[5]),
                    freq_offset=float(tokens[6]),
                    phase_offset=float(tokens[7]),
                )

        except Exception as e:
            raise RuntimeError(
                f"Line {line_number}: Invalid RF event `{line}`"
            ) from e

        rf_events.append(rf_event)

    return rf_events


def _parse_trap_gradients(lines: _LinesIterator) -> list[mrd.TrapezoidalGradient]:
    trap_gradients: list[mrd.TrapezoidalGradient] = []
    for line_number, line in lines.read_until_next_section():
        if line == "":
            continue
        tokens = line.split()
        try:
            trap_gradient = mrd.TrapezoidalGradient(
                id=int(tokens[0]),
                amp=float(tokens[1]),
                rise=int(tokens[2]),
                flat=int(tokens[3]),
                fall=int(tokens[4]),
                delay=int(tokens[5]),
            )
        except Exception as e:
            raise RuntimeError(
                f"Line {line_number}: Invalid trapezoidal gradient `{line}`"
            ) from e

        trap_gradients.append(trap_gradient)

    return trap_gradients


def _parse_arbitrary_gradients(
    lines: _LinesIterator, version
) -> list[mrd.ArbitraryGradient]:
    arbitrary_gradients: list[mrd.ArbitraryGradient] = []
    for line_number, line in lines.read_until_next_section():
        if line == "":
            continue
        tokens = line.split()
        try:
            if version >= _PULSEQ_VERSION_1_5_0:
                if len(tokens) != 7:
                    raise RuntimeError(
                        f"Line {line_number}: Invalid arbitrary gradient `{line}`"
                    )
                arbitrary_gradient = mrd.ArbitraryGradient(
                    id=int(tokens[0]),
                    amp=float(tokens[1]),
                    first=float(tokens[2]),
                    last=float(tokens[3]),
                    shape_id=int(tokens[4]),
                    time_id=int(tokens[5]),
                    delay=int(tokens[6]),
                )
            else:
                if len(tokens) != 5:
                    raise RuntimeError(
                        f"Line {line_number}: Invalid arbitrary gradient `{line}`"
                    )
                arbitrary_gradient = mrd.ArbitraryGradient(
                    id=int(tokens[0]),
                    amp=float(tokens[1]),
                    shape_id=int(tokens[2]),
                    time_id=int(tokens[3]),
                    delay=int(tokens[4]),
                )
            arbitrary_gradients.append(arbitrary_gradient)
        except Exception as e:
            raise RuntimeError(
                f"Line {line_number}: Invalid arbitrary gradient `{line}`"
            ) from e

    return arbitrary_gradients


def _parse_adc_events(lines: _LinesIterator, version) -> list[mrd.ADCEvent]:
    adc_events: list[mrd.ADCEvent] = []
    for line_number, line in lines.read_until_next_section():
        if line == "":
            continue
        tokens = line.split()
        try:
            if version >= _PULSEQ_VERSION_1_5_0:
                if len(tokens) != 9:
                    raise RuntimeError(
                        f"Line {line_number}: invalid ADC event `{line}`"
                    )
                adc_event = mrd.ADCEvent(
                    id=int(tokens[0]),
                    num=int(tokens[1]),
                    dwell=float(tokens[2]),
                    delay=int(tokens[3]),
                    freq_ppm=float(tokens[4]),
                    phase_ppm=float(tokens[5]),
                    freq=float(tokens[6]),
                    phase=float(tokens[7]),
                    phase_shape_id=int(tokens[8]),
                )
            else:
                if len(tokens) != 6:
                    raise RuntimeError(
                        f"Line {line_number}: invalid ADC event `{line}`"
                    )
            adc_event = mrd.ADCEvent(
                id=int(tokens[0]),
                num=int(tokens[1]),
                dwell=float(tokens[2]),
                delay=int(tokens[3]),
                freq=float(tokens[4]),
                phase=float(tokens[5]),
            )
        except Exception as e:
            raise RuntimeError(
                f"Line {line_number}: invalid ADC event `{line}`"
            ) from e

        adc_events.append(adc_event)

    return adc_events


def _parse_shapes(lines: _LinesIterator) -> list[mrd.Shape]:
    shapes: list[mrd.Shape] = []

    while True:
        lines.skip_empty_lines()
        peeked = lines.peek()
        if not peeked or peeked[1].startswith("[") and peeked[1].endswith("]"):
            break

        line_number, line = next(lines)
        k, v = line.split()
        if k != "shape_id" and k != "Shape_ID":
            raise RuntimeError(
                f"Line {line_number}: Expected shape_id, got `{line}`"
            )
        shape_id = int(v)

        line_number, line = next(lines)
        k, v = line.split()
        if k != "num_samples" and k != "Num_Uncompressed":
            raise RuntimeError(
                f"Line {line_number}: Expected num_samples, got `{line}`"
            )
        num_samples = int(v)

        data = []
        for line_number, line in lines:
            if line == "":
                break
            try:
                data.append(float(line))
            except ValueError:
                raise RuntimeError(
                    f"Line {line_number}: Invalid shape data `{line}`"
                )

        shapes.append(
            mrd.Shape(
                id=shape_id,
                num_samples=num_samples,
                data=np.array(data, dtype=np.float64),
            )
        )

    return shapes


def _parse_signature(lines: _LinesIterator) -> None:
    for _, line in lines:
        if line == "":
            break

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Converts a Pulseq .seq file into an MRD stream")
    parser.add_argument('-i', '--input', type=str, required=False, help="Input file, defaults to stdin")
    parser.add_argument('-o', '--output', type=str, required=False, help="Output file, defaults to stdout")
    args = parser.parse_args()

    with (open(args.input, "r") if args.input is not None else sys.stdin) as input:
        with (open(args.output, "wb") if args.output is not None else sys.stdout.buffer) as output:
            with mrd.BinaryMrdWriter(output) as writer:
                writer.write_header(None)
                writer.write_data(pulseq_text_to_stream_items(input))

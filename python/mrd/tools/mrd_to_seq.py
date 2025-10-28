import argparse
import sys
from typing import Iterable, TextIO, Tuple, Union
import warnings

import mrd

from mrd.tools.seq_to_mrd import (
    _PULSEQ_SUPPORTED_VERSIONS,
    _PULSEQ_VERSION_1_4_2,
    _PULSEQ_VERSION_1_5_0,
    _version_to_string,
)

_rf_use_to_abbreviation_dict = {e: e.name.lower()[0] for e in mrd.RFPulseUse}


def _get_abbreviation_for_rf_use(rf_use: mrd.RFPulseUse) -> str:
    try:
        return _rf_use_to_abbreviation_dict[rf_use]
    except KeyError:
        raise ValueError(f"Invalid RF use '{rf_use}'") from None


def _parse_version(version_str: str) -> Tuple[int, int, int]:
    parts = version_str.split(".")
    if len(parts) != 3:
        raise ValueError(f"Invalid version string: {version_str}")
    try:
        major, minor, patch = map(int, parts)
    except ValueError:
        raise ValueError(f"Invalid version string: {version_str}")
    return major, minor, patch


def stream_items_to_pulseq_text(
    items: Iterable[mrd.StreamItem],
    file: TextIO,
    version=_version_to_string(_PULSEQ_VERSION_1_4_2),
) -> None:
    parsed_version = _parse_version(version)

    definitions = mrd.PulseqDefinitions()
    blocks = []
    rf_events = []
    adc_events = []
    trap_grad_events = []
    arb_grad_events = []
    shapes = []

    for item in items:
        if isinstance(item, mrd.StreamItem.PulseqDefinitions):
            # If this is not the first occurrence of a Definition,
            # should we merge instead of replacing? Raise an error or warning?
            definitions = item.value
        elif isinstance(item, mrd.StreamItem.Blocks):
            blocks.extend(item.value)
        elif isinstance(item, mrd.StreamItem.Rf):
            rf_events.append(item.value)
        elif isinstance(item, mrd.StreamItem.Adc):
            adc_events.append(item.value)
        elif isinstance(item, mrd.StreamItem.TrapezoidalGradient):
            trap_grad_events.append(item.value)
        elif isinstance(item, mrd.StreamItem.ArbitraryGradient):
            arb_grad_events.append(item.value)
        elif isinstance(item, mrd.StreamItem.Shape):
            shapes.append(item.value)

    write_header(file)
    write_version(file, parsed_version)
    write_definitions(file, definitions)
    write_blocks(file, blocks)
    write_rf_events(file, rf_events, parsed_version)
    write_arbitrary_grad_events(file, arb_grad_events, parsed_version)
    write_trap_grad_events(file, trap_grad_events)
    write_adc_events(file, adc_events, parsed_version)
    write_shapes(file, shapes)


def write_header(file: TextIO) -> None:
    file.write("# Pulseq sequence file\n")
    file.write("# Created by MRD\n\n")


def write_version(file: TextIO, version: Tuple[int, int, int]) -> None:
    file.write("[VERSION]\n")
    file.write(f"major {version[0]}\n")
    file.write(f"minor {version[1]}\n")
    file.write(f"revision {version[2]}\n\n")


def write_definitions(file: TextIO, definitions: Union[mrd.PulseqDefinitions, None]) -> None:
    if definitions is None:
        raise ValueError("No definitions were present in the stream.")

    file.write("[DEFINITIONS]\n")
    file.write(f"AdcRasterTime {definitions.adc_raster_time:g}\n")
    file.write(f"BlockDurationRaster {definitions.block_duration_raster:g}\n")
    file.write(f"GradientRasterTime {definitions.gradient_raster_time:g}\n")
    file.write(f"RadiofrequencyRasterTime {definitions.radiofrequency_raster_time:g}\n")
    if definitions.name:
        file.write(f"Name {definitions.name}\n")
    if definitions.fov:
        file.write(
            f"FOV {definitions.fov.x:g} {definitions.fov.y:g} {definitions.fov.z:g}\n"
        )
    if definitions.total_duration:
        file.write(f"TotalDuration {definitions.total_duration:g}\n")
    for key, value in definitions.custom.items():
        file.write(f"{key} {value}\n")
    file.write("\n")


def write_blocks(file, blocks: list[mrd.Block]) -> None:
    file.write("# Format of blocks:\n")
    file.write("# NUM DUR RF  GX  GY  GZ  ADC  EXT\n")
    file.write("[BLOCKS]\n")

    id_width = len(str(len(blocks)))
    for block in blocks:
        file.write(
            f"{block.id:{id_width}d} "
            f"{block.duration:3d} {block.rf:3d} {block.gx:3d} {block.gy:3d} "
            f"{block.gz:3d} {block.adc:2d} {block.ext:2d}\n"
        )
    file.write("\n")


def write_arbitrary_grad_events(
    file, arb_grad_events: list[mrd.ArbitraryGradient], version
) -> None:
    if len(arb_grad_events) == 0:
        return

    if version >= _PULSEQ_VERSION_1_5_0:
        file.write("# Format of arbitrary gradients:\n")
        file.write(
            "#   time_shape_id of 0 means default timing "
            "(stepping with grad_raster starting at 1/2 of grad_raster)\n"
        )
        file.write("# id amplitude first last amp_shape_id time_shape_id delay\n")
        file.write("# ..      Hz/m  Hz/m Hz/m        ..         ..          us\n")
        file.write("[GRADIENTS]\n")

        "%d %12g %12g %12g %d %d %d"
        for grad in arb_grad_events:
            file.write(
                f"{grad.id:.0f} {grad.amp:12g} {grad.first:12g} {grad.last:12g} "
                f"{grad.shape_id:.0f} {grad.time_id:.0f} {grad.delay:.0f}\n"
            )
    else:
        file.write("# Format of arbitrary gradients:\n")
        file.write(
            "#   time_shape_id of 0 means default timing (stepping with grad_raster starting at 1/2 of grad_raster)\n"
        )
        file.write("# id amplitude amp_shape_id time_shape_id delay\n")
        file.write("# ..      Hz/m       ..         ..          us\n")
        file.write("[GRADIENTS]\n")
        for grad in arb_grad_events:
            if grad.first or grad.last:
                warnings.warn(f"Data loss when writing arbitrary gradient to pulseq version {_version_to_string(version)}")

            file.write(
                f"{grad.id:.0f} {grad.amp:12g} {grad.shape_id:.0f} {grad.time_id:.0f} {grad.delay:.0f}\n"
            )

    file.write("\n")


def write_trap_grad_events(
    file, trap_grad_events: list[mrd.TrapezoidalGradient]
) -> None:
    if len(trap_grad_events) == 0:
        return

    file.write("# Format of trapezoid gradients:\n")
    file.write("# id amplitude rise flat fall delay\n")
    file.write("# ..      Hz/m   us   us   us    us\n")
    file.write("[TRAP]\n")

    for grad in trap_grad_events:
        file.write(
            f"{grad.id:2d} {grad.amp:12g} {grad.rise:3.0f} "
            f"{grad.flat:4.0f} {grad.fall:3.0f} {grad.delay:3.0f}\n"
        )

    file.write("\n")


def write_rf_events(file, rf_events: list[mrd.RFEvent], version):
    if len(rf_events) == 0:
        return

    if version >= _PULSEQ_VERSION_1_5_0:
        file.write("# Format of RF events:\n")
        file.write(
            "# id ampl. mag_id phase_id time_shape_id center delay freqPPM phasePPM freq phase use\n"
        )
        file.write(
            "# ..   Hz      ..       ..            ..     us    us     ppm  rad/MHz   Hz   rad  ..\n"
        )
        file.write("[RF]\n")

        for rf in rf_events:
            file.write(
                f"{rf.id:.0f} {rf.amp:12g} {rf.mag_id:.0f} {rf.phase_id:.0f} {rf.time_id:.0f} "
                f"{rf.center:.0f} {rf.delay:g} {rf.freq_ppm:g} {rf.phase_ppm:g} "
                f"{rf.freq_offset:g} {rf.phase_offset:g} {_get_abbreviation_for_rf_use(rf.use)}\n"
            )
    else:
        file.write("# Format of RF events:\n")
        file.write("# id amplitude mag_id phase_id time_shape_id delay freq phase\n")
        file.write("# ..        Hz   ....     ....          ....    us   Hz   rad\n")
        file.write("[RF]\n")

        for rf in rf_events:
            if rf.center or rf.freq_ppm or rf.phase_ppm or rf.use != mrd.RFPulseUse.UNDEFINED:
                warnings.warn(f"Data loss when writing RF event to pulseq version {_version_to_string(version)}")

            file.write(
                f"{rf.id:.0f} {rf.amp:12g} {rf.mag_id:.0f} {rf.phase_id:.0f} {rf.time_id:.0f} "
                f"{rf.delay:g} {rf.freq_offset:g} {rf.phase_offset:g}\n"
            )

    file.write("\n")


def write_adc_events(file, adc_events: list[mrd.ADCEvent], version) -> None:
    if len(adc_events) == 0:
        return

    if version >= _PULSEQ_VERSION_1_5_0:
        file.write("# Format of ADC events:\n")
        file.write("# id num dwell delay freqPPM phasePPM freq phase phase_id\n")
        file.write("# ..  ..    ns    us     ppm  rad/MHz   Hz   rad       ..\n")
        file.write("[ADC]\n")

        for adc in adc_events:
            file.write(
                f"{adc.id:.0f} {adc.num:.0f} {adc.dwell:.0f} {adc.delay:.0f} {adc.freq_ppm:g} "
                f"{adc.phase_ppm:g} {adc.freq:g} {adc.phase:g} {adc.phase_shape_id:.0f}\n"
            )
    else:
        file.write("# Format of ADC events:\n")
        file.write("# id num dwell delay freq phase\n")
        file.write("# ..  ..    ns    us   Hz   rad\n")
        file.write("[ADC]\n")

        for adc in adc_events:
            if adc.freq_ppm or adc.phase_ppm or adc.phase_shape_id:
                warnings.warn(f"Data loss when writing ADC event to pulseq version {_version_to_string(version)}")

            file.write(
                f"{adc.id:.0f} {adc.num:.0f} {adc.dwell:.0f} {adc.delay:.0f} "
                f"{adc.freq:g} {adc.phase:g}\n"
            )

    file.write("\n")


def write_shapes(file, shapes: list[mrd.Shape]) -> None:
    if len(shapes) == 0:
        return

    file.write("# Sequence Shapes\n")
    file.write("[SHAPES]\n\n")

    for shape in shapes:
        file.write(f"shape_id {shape.id}\n")
        file.write(f"num_samples {shape.num_samples}\n")
        for sample in shape.data:
            file.write(f"{sample:0.9g}\n")
        file.write("\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parses a pulseq .seq file into MRD stream items")
    parser.add_argument('-i', '--input', type=str, required=False, help="Input file, defaults to stdin")
    parser.add_argument('-o', '--output', type=str, required=False, help="Output file, defaults to stdout")
    parser.add_argument(
        "-v",
        "--pulseq-version",
        metavar="version",
        type=str,
        required=False,
        help="Pulseq version to use, defaults to 1.4.2",
        choices=[_version_to_string(v) for v in _PULSEQ_SUPPORTED_VERSIONS],
        default=_version_to_string(_PULSEQ_VERSION_1_4_2),
    )
    args = parser.parse_args()

    with (open(args.input, "rb") if args.input is not None else sys.stdin.buffer) as input:
        with mrd.BinaryMrdReader(input) as reader:
            with (open(args.output, "w") if args.output is not None else sys.stdout) as output:
                reader.read_header()  # Ignore header
                stream_items_to_pulseq_text(reader.read_data(), output, args.pulseq_version)

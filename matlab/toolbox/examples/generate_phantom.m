function generate_phantom(output, kwargs)

arguments
    output (1,1) = 1

    kwargs.matrix_size (1,1) uint32 {mustBePositive} = 256
    kwargs.ncoils (1,1) uint32 {mustBePositive} = 8
    kwargs.oversampling (1,1) uint32 {mustBePositive} = 2
    kwargs.repetitions (1,1) uint32 {mustBePositive} = 1
    kwargs.acceleration (1,1) uint32 {mustBePositive} = 1
    kwargs.noise_level (1,1) single {mustBeNonnegative} = 0.05
    kwargs.calibration_width (1,1) uint32 {mustBeNonnegative} = 0
    kwargs.noise_calibration (1,1) logical = false
    kwargs.store_coordinates (1,1) logical = false
    kwargs.output_phantom (1,1) string = ""
    kwargs.output_csm (1,1) string = ""
    kwargs.output_coils (1,1) string = ""
end

nx = kwargs.matrix_size;
ny = kwargs.matrix_size;
nkx = kwargs.oversampling * nx;
nky = ny;
fov = 300;
slice_thickness = 5;

h = mrd.Header();

s = mrd.SubjectInformationType();
s.patient_id = "1234BGVF";
s.patient_name = "John Doe";
h.subject_information = s;

meas = mrd.MeasurementInformationType();
meas.patient_position = mrd.PatientPosition.H_FS;
h.measurement_information = meas;

sys_info = mrd.AcquisitionSystemInformationType();
sys_info.receiver_channels = kwargs.ncoils;
for c = 0:(kwargs.ncoils - 1)
    sys_info.coil_label(c + 1) = mrd.CoilLabelType(coil_number=c, coil_name="Channel " + string(c));
end
h.acquisition_system_information = sys_info;

exp = mrd.ExperimentalConditionsType();
exp.h1resonance_frequency_hz = 128000000;
h.experimental_conditions = exp;

e = mrd.EncodingSpaceType();
e.matrix_size = mrd.MatrixSizeType(x=nkx, y=nky, z=1);
e.field_of_view_mm = mrd.FieldOfViewMm(x=kwargs.oversampling*fov, y=fov, z=slice_thickness);

r = mrd.EncodingSpaceType();
r.matrix_size = mrd.MatrixSizeType(x=nx, y=ny, z=1);
r.field_of_view_mm = mrd.FieldOfViewMm(x=fov, y=fov, z=slice_thickness);

limits1 = mrd.LimitType();
limits1.minimum = 0;
limits1.center = idivide(ny, 2, "round");
limits1.maximum = ny - 1;

limits_rep = mrd.LimitType();
limits_rep.minimum = 0;
limits_rep.center = idivide(kwargs.repetitions, 2, "round");
limits_rep.maximum = kwargs.repetitions - 1;

limits = mrd.EncodingLimitsType();
limits.kspace_encoding_step_1 = limits1;
limits.repetition = limits_rep;

enc = mrd.EncodingType();
enc.trajectory = mrd.Trajectory.CARTESIAN;
enc.encoded_space = e;
enc.recon_space = r;
enc.encoding_limits = limits;

if kwargs.acceleration > 1
    p = mrd.ParallelImagingType();
    p.acceleration_factor.kspace_encoding_step_1 = kwargs.acceleration;
    p.acceleration_factor.kspace_encoding_step_2 = 1;
    p.calibration_mode = mrd.CalibrationMode.EMBEDDED;
    enc.parallel_imaging = p;
end

h.encoding(end+1) = enc;

phan = simulation.generate_shepp_logan_phantom(kwargs.matrix_size);
csm = simulation.generate_birdcage_sensitivities(kwargs.matrix_size, kwargs.ncoils);
coil_images = phan .* csm;

if kwargs.oversampling > 1
    nx = single(kwargs.matrix_size * kwargs.oversampling);
    coil_images = resize(coil_images, nx, Dimension=1, Side="both");
end

import mrd.binary.MrdWriter;

if kwargs.output_phantom ~= ""
    w = MrdWriter(kwargs.output_phantom);
    w.write_header(h);
    w.write_data(mrd.StreamItem.ArrayComplexFloat(phan));
    w.end_data();
    w.close();
end

if kwargs.output_csm ~= ""
    w = MrdWriter(kwargs.output_csm);
    w.write_header(h);
    w.write_data(mrd.StreamItem.ArrayComplexFloat(csm));
    w.end_data();
    w.close();
end

if kwargs.output_coils ~= ""
    w = MrdWriter(kwargs.output_coils);
    w.write_header(h);
    w.write_data(mrd.StreamItem.ArrayComplexFloat(coil_images));
    w.end_data();
    w.close();
end

coil_images = transform.image_to_kspace(coil_images, [1, 2]);

w = MrdWriter(output);
w.write_header(h);

acq = mrd.Acquisition();
acq.data = complex(zeros([nkx, kwargs.ncoils], 'single'));

acq.head.encoding_space_ref = 0;
acq.head.sample_time_ns = 5000;
acq.head.channel_order = (1:kwargs.ncoils) - 1;
acq.head.center_sample = idivide(nkx, 2, "round");
acq.head.read_dir(1) = 1;
acq.head.phase_dir(2) = 1;
acq.head.slice_dir(3) = 1;

scan_counter = 0;

if kwargs.noise_calibration
    % Write out a few noise scans
    for n = 1:32
        noise = generate_noise([nkx, kwargs.ncoils], kwargs.noise_level);
        % Here's where we would make the noise correlated
        acq.head.scan_counter = scan_counter;
        scan_counter = scan_counter + 1;
        acq.head.flags = mrd.AcquisitionFlags.IS_NOISE_MEASUREMENT;
        acq.data(:) = noise;
        w.write_data(mrd.StreamItem.Acquisition(acq));
    end
end

calib_start = idivide(nky, 2) - idivide(kwargs.calibration_width, 2);

for r = 0:kwargs.repetitions-1
    a = int32(mod(r, kwargs.acceleration));
    noise = generate_noise(size(coil_images), kwargs.noise_level);
    kspace = coil_images + noise;

    for line = 0:nky-1
        is_sampled_line = mod((int32(line) - a), int32(kwargs.acceleration)) == 0;
        in_calib_region = (line >= calib_start && line < calib_start + kwargs.calibration_width);
        if ~is_sampled_line && ~in_calib_region
            % Skip this line
            continue;
        end

        acq.head.scan_counter = scan_counter;
        scan_counter = scan_counter + 1;

        acq.head.flags = 0;
        if line == a
            acq.head.flags = mrd.AcquisitionFlags( ...
                    mrd.AcquisitionFlags.FIRST_IN_ENCODE_STEP_1, ...
                    mrd.AcquisitionFlags.FIRST_IN_SLICE, ...
                    mrd.AcquisitionFlags.FIRST_IN_REPETITION);
        elseif line >= nky - kwargs.acceleration
            acq.head.flags = mrd.AcquisitionFlags(...
                    mrd.AcquisitionFlags.LAST_IN_ENCODE_STEP_1, ...
                    mrd.AcquisitionFlags.LAST_IN_SLICE, ...
                    mrd.AcquisitionFlags.LAST_IN_REPETITION);
        elseif in_calib_region
            if ~is_sampled_line
                acq.head.flags = mrd.AcquisitionFlags.IS_PARALLEL_CALIBRATION;
            else
                acq.head.flags = mrd.AcquisitionFlags.IS_PARALLEL_CALIBRATION_AND_IMAGING;
            end
        end

        acq.head.idx.kspace_encode_step_1 = line;
        acq.head.idx.slice = 0;
        acq.head.idx.repetition = r;
        acq.data(:) = kspace(:, line+1, 1, :);

        if kwargs.store_coordinates
            acq.trajectory = zeros([nkx, 2], 'single');
            ky = (line - (nky / 2)) / nky;
            acq.trajectory(:, 1) = ((0:nkx-1) - (nkx / 2)) / nkx;
            acq.trajectory(:, 2) = ky;
        end

        w.write_data(mrd.StreamItem.Acquisition(acq));
    end
end

w.end_data();
w.close();
end

function noise = generate_noise(shape, noise_sigma, mean_)
    arguments
        shape {mustBeNumeric,mustBePositive}
        noise_sigma (1,1) {mustBeNumeric,mustBeNonnegative}
        mean_ (1,1) {mustBeNumeric} = 0
    end
    noise = randn(shape) + 1j * randn(shape);
    noise = noise .* noise_sigma + mean_;
    noise = single(noise);
end

function generate_phantom(output, kwargs)

arguments
    output (1,1) = 1

    kwargs.matrix_size (1,1) uint32 {mustBePositive} = 256
    kwargs.ncoils (1,1) uint32 {mustBePositive} = 8
    kwargs.oversampling (1,1) uint32 {mustBePositive} = 2
    kwargs.repetitions (1,1) uint32 {mustBePositive} = 1
    kwargs.noise_level (1,1) single {mustBeNonnegative} = 0.05
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

exp = mrd.ExperimentalConditionsType();
exp.h1resonance_frequency_hz = 128000000;
h.experimental_conditions = exp;

sys_info = mrd.AcquisitionSystemInformationType();
sys_info.receiver_channels = kwargs.ncoils;
h.acquisition_system_information = sys_info;

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
h.encoding(end+1) = enc;

phantom = generate_coil_kspace(kwargs.matrix_size, kwargs.ncoils, kwargs.oversampling);

import mrd.binary.MrdWriter;
w = MrdWriter(output);
w.write_header(h);

acq = mrd.Acquisition();
acq.data = complex(zeros([nkx, kwargs.ncoils], 'single'));

acq.head.channel_order = (1:kwargs.ncoils) - 1;
acq.head.center_sample = idivide(nkx, 2, "round");
acq.head.read_dir(1) = 1;
acq.head.phase_dir(2) = 1;
acq.head.slice_dir(3) = 1;

scan_counter = 0;

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

for r = 1:kwargs.repetitions
    noise = generate_noise(size(phantom), kwargs.noise_level);
    kspace = phantom + noise;

    for line = 1:nky
        acq.head.scan_counter = scan_counter;
        scan_counter = scan_counter + 1;

        acq.head.flags = 0;
        if line == 1
            acq.head.flags = mrd.AcquisitionFlags( ...
                    mrd.AcquisitionFlags.FIRST_IN_ENCODE_STEP_1, ...
                    mrd.AcquisitionFlags.FIRST_IN_SLICE, ...
                    mrd.AcquisitionFlags.FIRST_IN_REPETITION);
        elseif line == nky
            acq.head.flags = mrd.AcquisitionFlags(...
                    mrd.AcquisitionFlags.LAST_IN_ENCODE_STEP_1, ...
                    mrd.AcquisitionFlags.LAST_IN_SLICE, ...
                    mrd.AcquisitionFlags.LAST_IN_REPETITION);
        end

        acq.head.idx.kspace_encode_step_1 = line - 1;
        acq.head.idx.kspace_encode_step_2 = 0;
        acq.head.idx.slice = 0;
        acq.head.idx.repetition = r - 1;
        acq.data(:) = kspace(:, line, 1, :);
        w.write_data(mrd.StreamItem.Acquisition(acq));
    end
end

w.end_data();
w.close();
end

function kspace = generate_coil_kspace(matrix_size, ncoils, oversampling)
    phan = simulation.generate_shepp_logan_phantom(matrix_size);
    coils = simulation.generate_birdcage_sensitivities(matrix_size, ncoils);
    coils = phan .* coils;

    if oversampling > 1
        nx = single(matrix_size * oversampling);
        coils = resize(coils, nx, Dimension=1, Side="both");
    end
    kspace = transform.image_to_kspace(coils, [1, 2]);
end

function noise = generate_noise(shape, noise_sigma, mean_)
    arguments
        shape {mustBeNumeric,mustBePositive}
        noise_sigma (1,1) {mustBeNumeric,mustBePositive}
        mean_ (1,1) {mustBeNumeric} = 0
    end
    noise = randn(shape) + 1j * randn(shape);
    noise = noise .* noise_sigma + mean_;
    noise = single(noise);
end

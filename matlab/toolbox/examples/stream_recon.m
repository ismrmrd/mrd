function stream_recon(input, output)

arguments
    input (1,1) string
    output (1,1) = 1
end

import mrd.binary.MrdReader
import mrd.binary.MrdWriter
r = MrdReader(input);
w = MrdWriter(output);

header = r.read_header();
if header == yardl.None
    error("No header found in input file");
end

% Copy the header
w.write_header(header);

while r.has_data()
    item = r.read_data();

    if ~item.isAcquisition()
        continue
    end

    acq = item.value;

    if acq.flags.has_flags(mrd.AcquisitionFlags.IS_NOISE_MEASUREMENT)
        continue
    end

    if isempty(header.encoding)
        error("Encoding information missing from header");
    end

    enc = header.encoding(1);

    % Matrix size
    eNx = enc.encoded_space.matrix_size.x;
    eNy = enc.encoded_space.matrix_size.y;
    eNz = enc.encoded_space.matrix_size.z;
    rNx = enc.recon_space.matrix_size.x;
    rNy = enc.recon_space.matrix_size.y;
    rNz = enc.recon_space.matrix_size.z;

    % Field of view
    rFOVx = enc.recon_space.field_of_view_mm.x;
    rFOVy = enc.recon_space.field_of_view_mm.y;
    rFOVz = enc.recon_space.field_of_view_mm.z;
    if rFOVz == 0
        rFOVz = 1;
    end

    % Number of Slices, Reps, Contrasts, etc.
    ncoils = 1;
    if header.acquisition_system_information ~= yardl.None && header.acquisition_system_information.receiver_channels ~= yardl.None
        ncoils = header.acquisition_system_information.receiver_channels;
    end

    nslices = 1;
    ncontrasts = 1;
    ky_offset = 0;
    if enc.encoding_limits ~= yardl.None
        if enc.encoding_limits.slice ~= yardl.None
            nslices = enc.encoding_limits.slice.maximum + 1;
        end

        if enc.encoding_limits.contrast ~= yardl.None
            ncontrasts = enc.encoding_limits.contrast.maximum + 1;
        end

        if enc.encoding_limits.kspace_encoding_step_1 ~= yardl.None
            ky_offset = idivide(eNy + 1, 2) - enc.encoding_limits.kspace_encoding_step_1.center;
        end
    end

    if eNx ~= rNx && acq.samples() == eNx
        acq = remove_oversampling(enc, acq);
    end

    if acq.flags.has_flags(mrd.AcquisitionFlags.FIRST_IN_ENCODE_STEP_1) || acq.flags.has_flags(mrd.AcquisitionFlags.FIRST_IN_SLICE)
        acq_shape = size(acq.data);
        if acq_shape(1) == eNx
            readout_length = eNx;
        else
            readout_length = rNx;   % Readout oversampling has been removed upstream
        end
        buffer = zeros(readout_length, rNy, rNz, ncoils, nslices, ncontrasts, 'single');
        ref_acq = acq;
    end

    contrast = 1;
    slice = 1;
    k1 = 1;
    k2 = 1;
    if acq.idx.contrast ~= yardl.None
        contrast = acq.idx.contrast + 1;
    end
    if acq.idx.slice ~= yardl.None
        slice = acq.idx.slice + 1;
    end
    if acq.idx.kspace_encode_step_1 ~= yardl.None
        k1 = acq.idx.kspace_encode_step_1 + 1;
    end
    if acq.idx.kspace_encode_step_2 ~= yardl.None
        k2 = acq.idx.kspace_encode_step_2 + 1;
    end

    buffer(:, k1 + ky_offset, k2, :, slice, contrast) = acq.data;

    if acq.flags.has_flags(mrd.AcquisitionFlags.LAST_IN_ENCODE_STEP_1) || acq.flags.has_flags(mrd.AcquisitionFlags.LAST_IN_SLICE)
        buf_shape = size(buffer);
        if buf_shape(3) > 1
            img = transform.kspace_to_image(buffer, [1, 2, 3]);
        else
            img = transform.kspace_to_image(buffer, [1, 2]);
        end

        for icontrast = 1:ncontrasts
            for islice = 1:nslices
                slice = img(:,:,:,:,islice,icontrast);
                combined = squeeze(sqrt(abs(sum(slice .* conj(slice), 4))));

                combined_shape = size(combined);
                xoff = floor((combined_shape(1) + 1) / 2) - idivide((rNx + 1), 2);
                yoff = floor((combined_shape(2) + 1) / 2) - idivide((rNy + 1), 2);
                if ndims(combined) == 3
                    zoff = floor((combined_shape(3) + 1) / 2) - idivide((rNz + 1), 2);
                    combined = combined(1+xoff:xoff+rNx, 1+yoff:yoff+rNy, 1+zoff:zoff+rNz);
                elseif ndims(combined) == 2
                    combined = combined(1+xoff:xoff+rNx, 1+yoff:yoff+rNy);
                else
                    error("Image should have 2 or 3 dimensions");
                end

                mrd_image = mrd.ImageFloat(data=combined, image_type=mrd.ImageType.MAGNITUDE);

                mrd_image.field_of_view(1) = rFOVx;
                mrd_image.field_of_view(2) = rFOVy;
                mrd_image.field_of_view(3) = single(rFOVz) ./ single(rNz);
                mrd_image.position = ref_acq.position;
                mrd_image.col_dir = ref_acq.read_dir;
                mrd_image.line_dir = ref_acq.phase_dir;
                mrd_image.slice_dir = ref_acq.slice_dir;
                mrd_image.patient_table_position = ref_acq.patient_table_position;
                mrd_image.acquisition_time_stamp = ref_acq.acquisition_time_stamp;
                mrd_image.physiology_time_stamp = ref_acq.physiology_time_stamp;
                mrd_image.slice = ref_acq.idx.slice;
                mrd_image.contrast = contrast;
                mrd_image.repetition = ref_acq.idx.repetition;
                mrd_image.phase = ref_acq.idx.phase;
                mrd_image.average = ref_acq.idx.average;
                mrd_image.set = ref_acq.idx.set;

                w.write_data(mrd.StreamItem.ImageFloat(mrd_image));
            end
        end
        buffer = nan;
        ref_acq = nan;
    end
end
w.end_data();
r.close();
w.close();
end


function out = remove_oversampling(encoding, acq)
    eNx = encoding.encoded_space.matrix_size.x;
    rNx = encoding.recon_space.matrix_size.x;

    out = acq;
    xline = transform.kspace_to_image(acq.data, [1]);
    x0 = idivide((eNx - rNx), 2) + 1;
    x1 = x0 + rNx - 1;
    xline = xline(x0:x1, :);
    out.center_sample = idivide(rNx, 2);
    out.data = transform.image_to_kspace(xline, [1]);
end

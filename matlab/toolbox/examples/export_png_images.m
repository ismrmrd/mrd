function export_png_images(input, kwargs)
    arguments
        input (1,1) string
        kwargs.output_prefix (1,1) string = "image_"
        kwargs.show (1,1) logical = false
    end

    save = @imwrite;
    if kwargs.show
        save = @imwrite_and_show;
    end

    import mrd.binary.MrdReader
    r = MrdReader(input);

    header = r.read_header();
    if header == yardl.None
        error("No header found in input file");
    end

    image_counter = 0;
    while r.has_data()
        item = r.read_data();

        if ~item.isImageFloat()
            error("Stream must contain only floating point images");
        end

        image = item.value;

        image.data = image.data ./ max(image.data(:));

        if ismatrix(image.data)
            save(transpose(image.data), sprintf("%s%04d.png", kwargs.output_prefix, image_counter));
            image_counter = image_counter + 1;
        elseif ndims(image.data) == 3
            shape = size(image.data);
            for s = 1:shape(3)
                save(transpose(image.data(:,:,s)), sprintf("%s%04d.png", kwargs.output_prefix, image_counter));
                image_counter = image_counter + 1;
            end
        else
            for c = 1:image.channels()
                for s = 1:image.slices()
                    save(transpose(image.data(:,:,s,c)), sprintf("%s%04d.png", kwargs.output_prefix, image_counter));
                    image_counter = image_counter + 1;
                end
            end
        end
    end

    if kwargs.show
        % Wait for all figure windows to be closed
        uiwait;
    end
end

function imwrite_and_show(image_data, filename)
    figure;
    imshow(image_data);
    imwrite(image_data, filename);
end

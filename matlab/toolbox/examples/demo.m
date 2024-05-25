% Simple demonstration of the MATLAB example tools

function demo()
    % Add the toolbox packages to the path
    addpath("../");

    phantom = "phantom.bin";
    images = "images.bin";

    generate_phantom(phantom, repetitions=3, oversampling=2);
    stream_recon(phantom, images);
    export_png_images(images, show=false);
end

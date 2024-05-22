classdef MrdTest < matlab.unittest.TestCase
    methods (Test)

        function testMinimalExample(testCase)
            addpath("../toolbox", "../toolbox/examples");

            minimal_example();

            delete("./*.bin");
        end

        function testFullRecon(testCase)
            addpath("../toolbox", "../toolbox/examples");

            phantom = "phantom.bin";
            images = "images.bin";

            generate_phantom(phantom, matrix_size=128, ncoils=12, oversampling=3, repetitions=2);
            stream_recon(phantom, images);
            export_png_images(images, show=false);

            delete("./*.bin");
            delete("./*.png");
        end

    end
end

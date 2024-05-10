function coil_sensitivities = generate_birdcage_sensitivities(matrix_size, ncoils, relative_radius)
    % Generates birdcage coil sensitivities.
    %
    % This function is heavily inspired by the mri_birdcage.m Matlab script in
    % Jeff Fessler's IRT package: http://web.eecs.umich.edu/~fessler/code/
    %
    % Parameters
    % ----------
    % matrix_size: int
    %     Size of imaging matrix in pixels
    % ncoils: int
    %     Number of simulated coils
    % relative_radius: single, optional
    %     Relative radius of birdcage (default 1.5)
    %
    % Returns
    % -------
    % complex single array with shape (matrix_size, matrix_size, 1, ncoils)
    arguments
        matrix_size (1,1) single {mustBePositive}
        ncoils (1,1) single {mustBePositive}
        relative_radius (1,1) single = 1.5
    end

    shape = [matrix_size, matrix_size, 1, ncoils];
    coil_sensitivities = complex(zeros(shape, 'single'));
    m = matrix_size ./ 2;
    for c = 1:ncoils
        coilx = relative_radius * cos((c-1) * (2 * pi / ncoils));
        coily = relative_radius * sin((c-1) * (2 * pi / ncoils));
        coil_phase = -1.0 * (c-1) * (2 * pi / ncoils);
        for y = 1:matrix_size
            y_co = (y-1 - m) / m - coily;
            for x = 1:matrix_size
                x_co = (x-1 - m) / m - coilx;
                rr = sqrt(x_co * x_co + y_co * y_co);
                phi = atan2(x_co, -y_co) + coil_phase;
                coil_sensitivities(x, y, 1, c) = complex(1 / rr * cos(phi), 1 / rr * sin(phi));
            end
        end
    end
end

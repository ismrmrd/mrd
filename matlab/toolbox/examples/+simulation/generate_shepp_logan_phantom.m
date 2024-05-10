function phantom = generate_shepp_logan_phantom(matrix_size)
    phantom = generate(matrix_size, modified_shepp_logan_ellipses());
end

function phantom = generate(matrix_size, ellipses)
    % Create a Shepp-Logan or modified Shepp-Logan phantom:
    %
    %     phantom = generate(256, shepp_logan_ellipses());
    %
    % Parameters
    % ----------
    % matrix_size: int
    %     Size of imaging matrix in pixels
    %
    % ellipses: array of PhantomEllipse
    %     Custom set of ellipses to use.
    %
    % Returns
    % -------
    % complex single array with shape [matrix_size, matrix_size]
    %
    % Notes
    % -----
    % The image bounding box in the algorithm is ``[-1, -1], [1, 1]``,
    % so the values of ``a``, ``b``, ``x0``, ``y0`` should all be specified with
    % respect to this box.
    %
    % References:
    %
    % Shepp, L. A.; Logan, B. F.; Reconstructing Interior Head Tissue
    % from X-Ray Transmissions, IEEE Transactions on Nuclear Science,
    % Feb. 1974, p. 232.
    %
    % Toft, P.; "The Radon Transform - Theory and Implementation",
    % Ph.D. thesis, Department of Mathematical Modelling, Technical
    % University of Denmark, June 1996.
    arguments
        matrix_size (1,1) single {mustBePositive}
        ellipses {mustBeA(ellipses, 'simulation.PhantomEllipse')}
    end

    phantom = zeros(matrix_size, 'single');
    m = matrix_size ./ 2;
    for e = 1:length(ellipses)
        ellipse = ellipses(e);
        for y = 1:matrix_size
            y_co = (y-1 - m) ./ m;
            for x = 1:matrix_size
                x_co = (x-1 - m) ./ m;
                if ellipse.is_inside(x_co, y_co)
                    phantom(x, y) = phantom(x, y) + ellipse.get_amplitude() + 0.j;
                end
            end
        end
    end
    phantom = complex(phantom);
end


function ellipses = shepp_logan_ellipses()
    import simulation.PhantomEllipse;
    % Standard head phantom, taken from Shepp & Logan
    ellipses = [
        PhantomEllipse(1.0, 0.6900, 0.9200, 0.00, 0.0000, 0.0),
        PhantomEllipse(-0.98, 0.6624, 0.8740, 0.00, -0.0184, 0.0),
        PhantomEllipse(-0.02, 0.1100, 0.3100, 0.22, 0.0000, -18.0),
        PhantomEllipse(-0.02, 0.1600, 0.4100, -0.22, 0.0000, 18.0),
        PhantomEllipse(0.01, 0.2100, 0.2500, 0.00, 0.3500, 0.0),
        PhantomEllipse(0.01, 0.0460, 0.0460, 0.00, 0.1000, 0.0),
        PhantomEllipse(0.01, 0.0460, 0.0460, 0.00, -0.1000, 0.0),
        PhantomEllipse(0.01, 0.0460, 0.0230, -0.08, -0.6050, 0.0),
        PhantomEllipse(0.01, 0.0230, 0.0230, 0.00, -0.6060, 0.0),
        PhantomEllipse(0.01, 0.0230, 0.0460, 0.06, -0.6050, 0.0),
    ];
end

function ellipses =  modified_shepp_logan_ellipses()
    import simulation.PhantomEllipse;
    % Modified version of Shepp & Logan's head phantom, adjusted to improve contrast. Taken from Toft.
    ellipses = [
        PhantomEllipse(1.0, .6900, .9200, 0.00, 0.0000, 0.0),
        PhantomEllipse(-0.8, .6624, .8740, 0.00, -0.0184, 0.0),
        PhantomEllipse(-0.2, .1100, .3100, 0.22, 0.0000, -18.0),
        PhantomEllipse(-0.2, .1600, .4100, -0.22, 0.0000, 18.0),
        PhantomEllipse(0.1, .2100, .2500, 0.00, 0.3500, 0.0),
        PhantomEllipse(0.1, .0460, .0460, 0.00, 0.1000, 0.0),
        PhantomEllipse(0.1, .0460, .0460, 0.00, -0.1000, 0.0),
        PhantomEllipse(0.1, .0460, .0230, -0.08, -0.6050, 0.0),
        PhantomEllipse(0.1, .0230, .0230, 0.00, -0.6060, 0.0),
        PhantomEllipse(0.1, .0230, .0460, 0.06, -0.6050, 0.0),
    ];
end

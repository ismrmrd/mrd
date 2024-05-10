classdef PhantomEllipse < handle
    % Ellipse object for phantom generation
    %
    % Properties
    % ----------
    % A: float
    %     Additive intensity of the ellipse.
    % a: float
    %     Length of the major axis.
    % b: float
    %     Length of the minor axis.
    % x0: float
    %     Horizontal offset of the centre of the ellipse.
    % y0: float
    %     Vertical offset of the centre of the ellipse.
    % phi: float
    %     Counterclockwise rotation of the ellipse in degrees,
    %     measured as the angle between the horizontal axis and
    %     the ellipse major axis.

    properties
        A
        a
        b
        x0
        y0
        phi
    end

    methods
        function obj = PhantomEllipse(A, a, b, x0, y0, phi)
            obj.A = A;
            obj.a = a;
            obj.b = b;
            obj.x0 = x0;
            obj.y0 = y0;
            obj.phi = phi;
        end

        function inside = is_inside(obj, x, y)
            asq = obj.a * obj.a;
            bsq = obj.b * obj.b;
            phi = obj.phi * pi / 180;
            x0 = x - obj.x0;
            y0 = y - obj.y0;
            cosp = cos(phi);
            sinp = sin(phi);
            inside = ...
                ((x0 * cosp + y0 * sinp) * (x0 * cosp + y0 * sinp)) / asq + ...
                ((y0 * cosp - x0 * sinp) * (y0 * cosp - x0 * sinp)) / bsq ...
                <= 1;
        end

        function amplitude = get_amplitude(obj)
            amplitude = obj.A;
        end
    end
end

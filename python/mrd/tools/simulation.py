"""
Tools for generating coil sensitivities and phantoms
"""
import numpy as np
import numpy.typing as npt
from mrd.tools.transform import kspace_to_image, image_to_kspace


def generate_shepp_logan_phantom(matrix_size) -> npt.NDArray[np.complex64]:
    """Generates a modified Shepp Logan phantom with improved contrast"""
    return generate_phantom(matrix_size, modified_shepp_logan_ellipses())


def generate_phantom(matrix_size, ellipses) -> npt.NDArray[np.complex64]:
    """
    Create a Shepp-Logan or modified Shepp-Logan phantom::

        phantom (n = 256, phantom_type = 'Modified Shepp-Logan', ellipses = None)

    Parameters
    ----------
    matrix_size: int
        Size of imaging matrix in pixels

    ellipses: list of PhantomEllipse
        Custom set of ellipses to use.

    Returns
    -------
    np.ndarray
        Phantom image with shape (1, 1, matrix_size, matrix_size)

    Notes
    -----
    The image bounding box in the algorithm is ``[-1, -1], [1, 1]``,
    so the values of ``a``, ``b``, ``x0``, ``y0`` should all be specified with
    respect to this box.

    References:

    Shepp, L. A.; Logan, B. F.; Reconstructing Interior Head Tissue
    from X-Ray Transmissions, IEEE Transactions on Nuclear Science,
    Feb. 1974, p. 232.

    Toft, P.; "The Radon Transform - Theory and Implementation",
    Ph.D. thesis, Department of Mathematical Modelling, Technical
    University of Denmark, June 1996.
    """
    shape = (1, 1, matrix_size, matrix_size)
    out = np.zeros(shape, dtype=np.complex64)
    for e in ellipses:
        for y in range(matrix_size):
            y_co = (float(y) - (matrix_size >> 1))  / (matrix_size >> 1)
            for x in range(matrix_size):
                x_co = (float(x) - (matrix_size >> 1))  / (matrix_size >> 1)
                if e.is_inside(x_co, y_co):
                    out[0, 0, y, x] += e.get_amplitude() + 0.j
    return out

def generate_birdcage_sensitivities(matrix_size, ncoils, relative_radius=1.5) -> npt.NDArray[np.complex64]:
    """Generates birdcage coil sensitivities.

    This function is heavily inspired by the mri_birdcage.m Matlab script in
    Jeff Fessler's IRT package: http://web.eecs.umich.edu/~fessler/code/

    Parameters
    ----------
    matrix_size: int
        Size of imaging matrix in pixels
    ncoils: int
        Number of simulated coils
    relative_radius: float, optional
        Relative radius of birdcage (default 1.5)

    Returns
    -------
    np.ndarray
        Birdcage coil sensitivities with shape (ncoils, 1, matrix_size, matrix_size)
    """
    shape = (ncoils, 1, matrix_size, matrix_size)
    out = np.zeros(shape, dtype=np.complex64)
    for c in range(ncoils):
        coilx = relative_radius * np.cos(c * (2 * np.pi / ncoils))
        coily = relative_radius * np.sin(c * (2 * np.pi / ncoils))
        coil_phase = -1.0 * c * (2 * np.pi / ncoils)
        for y in range(matrix_size):
            y_co = (float(y) - (matrix_size >> 1)) / (matrix_size >> 1) - coily
            for x in range(matrix_size):
                x_co = (float(x) - (matrix_size >> 1)) / (matrix_size >> 1) - coilx
                rr = np.sqrt(x_co * x_co + y_co * y_co)
                phi = np.arctan2(x_co, -y_co) + coil_phase
                out[c, 0, y, x] = complex(1 / rr * np.cos(phi), 1 / rr * np.sin(phi))
    return out


class PhantomEllipse:
    """Ellipse object for phantom generation"""

    def __init__(self, A, a, b, x0, y0, phi):
        """Construct a PhantomEllipse

        Parameters
        ----------
        A: float
            Additive intensity of the ellipse.
        a: float
            Length of the major axis.
        b: float
            Length of the minor axis.
        x0: float
            Horizontal offset of the centre of the ellipse.
        y0: float
            Vertical offset of the centre of the ellipse.
        phi: float
            Counterclockwise rotation of the ellipse in degrees,
            measured as the angle between the horizontal axis and
            the ellipse major axis.
        """
        self.A = A
        self.a = a
        self.b = b
        self.x0 = x0
        self.y0 = y0
        self.phi = phi

    def is_inside(self, x, y):
        """Determine whether an (x,y) coordinate is inside the ellipse"""
        asq = self.a * self.a
        bsq = self.b * self.b
        phi = self.phi * np.pi / 180
        x0 = x - self.x0
        y0 = y - self.y0
        cosp = np.cos(phi)
        sinp = np.sin(phi)
        return (
            ((x0 * cosp + y0 * sinp) * (x0 * cosp + y0 * sinp)) / asq +
            ((y0 * cosp - x0 * sinp) * (y0 * cosp - x0 * sinp)) / bsq
            <= 1)

    def get_amplitude(self):
        return self.A


def shepp_logan_ellipses():
    """Standard head phantom, taken from Shepp & Logan"""
    return [
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
    ]

def modified_shepp_logan_ellipses():
    """Modified version of Shepp & Logan's head phantom, adjusted to
    improve contrast. Taken from Toft.
    """
    return [
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
    ]

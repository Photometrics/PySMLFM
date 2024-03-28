from enum import Enum, unique

import numpy as np
import numpy.typing as npt


class MicroLensArray:
    """A class describing micro-lens array.

    Attributes:
        lattice_type (LatticeType): A lens arrangement.
        focal_length (float): A focal length of micro-lenses (in mm).
        lens_pitch (float):
            A pitch along X direction, parallel with optical table (in microns).
        optic_size (float):
            A physical size of the array, assumes a square optic (in microns).
        centre (npt.NDArray[float]):
            A spatial X,Y position in terms of camera space
            (in lattice spacing units).

        lens_centres (npt.NDArray[float]):
            An array of X,Y lens centres (in lattice spacing units).
    """

    @unique
    class LatticeType(Enum):
        HEXAGONAL = 1
        SQUARE = 2

    def __init__(self,
                 lattice_type: LatticeType,
                 focal_length: float,
                 lens_pitch: float,
                 optic_size: float,
                 centre: npt.NDArray[float]):
        """Constructs the micro-lens array object.

        Args:
            lattice_type (LatticeType): Lens arrangement.
            focal_length (float): A focal length of micro-lenses (in mm).
            lens_pitch (float):
                A pitch along X direction, parallel with optical table
                (in microns).
            optic_size (float):
                A physical size of the array, assumes it is a square optic
                (in microns).
            centre (npt.NDArray[float]):
                A spatial X, Y position in terms of camera space
                (in lattice spacing units).
        """

        self.lattice_type = lattice_type
        self.focal_length = focal_length
        self.lens_pitch = lens_pitch
        self.optic_size = optic_size
        self.centre = centre

        self.lens_centres = self._generate_lattice()

    def _generate_lattice(self) -> npt.NDArray[float]:
        """Generate the X,Y lattice coordinates based on given pattern."""

        if self.lattice_type == MicroLensArray.LatticeType.SQUARE:
            # Generate centers of square lenses, pretending pitch is 1.
            # Generate more than needed, because gets cropped when rotated.

            width = self.optic_size / self.lens_pitch
            marks = np.arange(-np.floor(width / 2), np.ceil(width / 2) + 1)
            x, y = np.meshgrid(marks, marks)

        elif self.lattice_type == MicroLensArray.LatticeType.HEXAGONAL:
            # Generate centers of hexagonal lenses, pretending pitch is 1.
            # Generate more than needed, because gets cropped when rotated.

            width = self.optic_size / self.lens_pitch
            marks = np.arange(-np.floor(width / 2), np.ceil(width / 2) + 1)
            xx, yy = np.meshgrid(marks, marks)

            length = np.max(xx.shape)
            dx = np.tile([0.5, 0], [length, np.ceil(length / 2).astype(int)])
            dx = dx[0:length, 0:length]  # TODO: Is this necessary?
            x = yy * np.sqrt(3) / 2
            y = xx + dx.T + 0.5

        else:
            raise ValueError(f'Unsupported lattice type with value {self.lattice_type}')

        return np.column_stack((x.flatten('F'), y.flatten('F')))

    def offset_lattice(self,
                       dxy: npt.NDArray[float]
                       ) -> None:
        """Shift the coordinates of the micro-lenses centers.

        Args:
            dxy (npt.NDArray[float]): A shift in X and Y directions
                (in lattice spacing units).
        """

        self.lens_centres[:] += dxy

        # TODO: Should the MLA centre be moved as well?
        #       If yes, it negates the move effect...
        # self.centre += dxy

    def rotate_lattice(self,
                       theta: float
                       ) -> None:
        """Rotate the coordinates of the micro-lenses centers around the centre.

        Args:
            theta (float): An angle to rotate (in radians).
        """

        # Shift centre to origin
        x = self.lens_centres[:, 0] - self.centre[0]
        y = self.lens_centres[:, 1] - self.centre[1]
        # Rotate around origin
        self.lens_centres[:, 0] = (x * np.cos(theta) - y * np.sin(theta))
        self.lens_centres[:, 1] = (x * np.sin(theta) + y * np.cos(theta))
        # Shift origin back to centre
        self.lens_centres[:, 0] += self.centre[0]
        self.lens_centres[:, 1] += self.centre[1]

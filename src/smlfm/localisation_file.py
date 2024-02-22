from enum import Enum, unique
from pathlib import Path

import numpy as np
import numpy.typing as npt


class LocalisationFile:
    """A wrapper class around localisation files.

    It serves as a namespace for localisation file related types only."""

    @unique
    class Format(Enum):
        PEAKFIT = 1
        THUNDERSTORM = 2
        PICASSO = 3

    @staticmethod
    def read(csv_file: Path,
             file_format: Format,
             pixel_size_sample: float
             ) -> npt.NDArray[float]:
        """Parses given file and returns the data as a matrix.

        Args:
            csv_file (Path): A file name with path to parse.
            file_format (Format): A format of the given file.
            pixel_size_sample (float): A pixel size in sample space (in microns).

        Returns:
            A 2D array (npt.NDArray[float]) filled with the data from given
            file. It contains the localised maxima in rows, where each has
            8 columns.

            * [0] frame number (int)
            * [1] X coordinate (in microns)
            * [2] Y coordinate (in microns)
            * [3] sigma X (in microns)
            * [4] sigma Y (in microns)
            * [5] intensity (in photons)
            * [6] background intensity (in photons)
            * [7] precision or uncertainty (in microns)
        """

        if file_format == LocalisationFile.Format.PICASSO:
            id_frame = 1       # column index with frame number
            id_x = 2           # column index with X coordinates (in nm)
            id_y = 3           # column index with Y coordinates (in nm)
            id_sigma_x = 4     # column index with sigma X (in nm)
            id_sigma_y = 4     # column index with sigma Y (in nm)
            id_intensity = 5   # column index with intensity (in photons)
            id_background = 6  # column index with background (in photons)
            id_precision = 8   # column index with precision or uncertainty (in nm)
            scale_xy = 1000    # scale coordinates to microns
            scale_pr = 1000    # scale precision to microns
        elif file_format == LocalisationFile.Format.THUNDERSTORM:
            id_frame = 0       # column index with frame number
            id_x = 1           # column index with X coordinates (in nm)
            id_y = 2           # column index with Y coordinates (in nm)
            id_sigma_x = 3     # column index with sigma X (in nm)
            id_sigma_y = 3     # column index with sigma Y (in nm)
            id_intensity = 4   # column index with intensity (in photons)
            id_background = 5  # column index with background (in photons)
            id_precision = 6   # column index with precision or uncertainty (in nm)
            scale_xy = 1000    # scale coordinates to microns
            scale_pr = 1000    # scale precision to microns
        elif file_format == LocalisationFile.Format.PEAKFIT:
            id_frame = 0       # column index with frame number
            id_x = 9           # column index with X coordinates (in pixels)
            id_y = 10          # column index with Y coordinates (in pixels)
            id_sigma_x = 12    # column index with sigma X (in pixels)
            id_sigma_y = 12    # column index with sigma Y (in pixels)
            id_intensity = 8   # column index with intensity (in photons)
            id_background = 7  # column index with background (in photons)
            id_precision = 13  # column index with precision or uncertainty (in nm)
            scale_xy = 1 / pixel_size_sample  # scale coordinates to microns
            scale_pr = 1000    # scale precision to microns
        else:
            raise ValueError(f'Unsupported localisation file format with value'
                             f' {file_format}')

        raw_data = np.genfromtxt(csv_file, delimiter=',', dtype=float)

        data = np.empty((raw_data.shape[0], 8))
        data.fill(np.nan)
        data[:, 0] = raw_data[:, id_frame]
        data[:, 1] = raw_data[:, id_x] / scale_xy
        data[:, 2] = raw_data[:, id_y] / scale_xy
        data[:, 3] = raw_data[:, id_sigma_x] / scale_xy
        data[:, 4] = raw_data[:, id_sigma_y] / scale_xy
        data[:, 5] = raw_data[:, id_intensity]
        data[:, 6] = raw_data[:, id_background]
        data[:, 7] = raw_data[:, id_precision] / scale_pr

        return data

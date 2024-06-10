from enum import Enum, unique
from pathlib import Path
from typing import Optional

import numpy as np
import numpy.typing as npt


class LocalisationFile:
    """A wrapper class around localisation files.

    Attributes:
        csv_file (Path): A file name with path to parse.
        file_format (Format): A format of the given file.
        pixel_size (float):
            A pixel size in sample space (in microns), defaults to 1.0.
        data (npt.NDArray[float]):
            A 2D array filled with the data from given file.
            It contains the localised maxima in rows, where each has 8 columns.

            * [0] frame number (int)
            * [1] X coordinate (in microns)
            * [2] Y coordinate (in microns)
            * [3] sigma X (in microns)
            * [4] sigma Y (in microns)
            * [5] intensity (in photons)
            * [6] background intensity (in photons)
            * [7] precision or uncertainty (in microns)

            The `PEAKFIT` file format has data in columns 1 to 4 in pixels,
            not microns. The `scale_peakfit_data()` function should be called
            with a scale factor that converts the value from pixels to microns.
    """

    @unique
    class Format(Enum):
        PEAKFIT = 1
        THUNDERSTORM = 2
        PICASSO = 3

    def __init__(self,
                 csv_file: Path,
                 file_format: Format):
        """Constructs the localisation file wrapper.

        Args:
            csv_file (Path): A file name with path to parse.
            file_format (Format): A format of the given file.
        """

        self.csv_file = csv_file
        self.file_format = file_format
        self.pixel_size: float = 1.0
        self.data: Optional[npt.NDArray[float]] = None

        self._raw_data: Optional[npt.NDArray[float]] = None

    def read(self) -> None:
        """Parses the CSV file."""

        self.pixel_size = 1.0
        self.data = None
        self._raw_data = None

        if self.file_format == LocalisationFile.Format.PICASSO:
            id_frame = 1       # column index with frame number
            id_x = 2           # column index with X coordinates (in nm)
            id_y = 3           # column index with Y coordinates (in nm)
            id_sigma_x = 4     # column index with sigma X (in nm)
            id_sigma_y = 4     # column index with sigma Y (in nm)
            id_intensity = 5   # column index with intensity (in photons)
            id_background = 6  # column index with background (in photons)
            id_precision = 8   # column index with precision or uncertainty (in nm)
            min_columns = 9
            scale_xy = 1000    # scale coordinates to microns
            scale_pr = 1000    # scale precision to microns
        elif self.file_format == LocalisationFile.Format.THUNDERSTORM:
            id_frame = 0       # column index with frame number
            id_x = 1           # column index with X coordinates (in nm)
            id_y = 2           # column index with Y coordinates (in nm)
            id_sigma_x = 3     # column index with sigma X (in nm)
            id_sigma_y = 3     # column index with sigma Y (in nm)
            id_intensity = 4   # column index with intensity (in photons)
            id_background = 5  # column index with background (in photons)
            id_precision = 6   # column index with precision or uncertainty (in nm)
            min_columns = 7
            scale_xy = 1000    # scale coordinates to microns
            scale_pr = 1000    # scale precision to microns
        elif self.file_format == LocalisationFile.Format.PEAKFIT:
            # Reset scale factor, must be applied again on new data
            self.pixel_size = 1.0
            id_frame = 0       # column index with frame number
            id_x = 9           # column index with X coordinates (in pixels)
            id_y = 10          # column index with Y coordinates (in pixels)
            id_sigma_x = 12    # column index with sigma X (in pixels)
            id_sigma_y = 12    # column index with sigma Y (in pixels)
            id_intensity = 8   # column index with intensity (in photons)
            id_background = 7  # column index with background (in photons)
            id_precision = 13  # column index with precision or uncertainty (in nm)
            min_columns = 14
            scale_xy = 1       # scale coordinates to microns (to be set yet)
            scale_pr = 1000    # scale precision to microns
        else:
            raise ValueError(f'Unsupported localisation file format with value'
                             f' {self.file_format}')

        csv_header_rows = 0
        csv_delimiter = None  # Default delimiter (whitespaces)
        max_line_len = 16384
        with open(self.csv_file, 'r', encoding='utf-8') as f:
            while True:
                line = f.readline(max_line_len)
                if not line:
                    break  # No data in file
                if line[-1] != '\n' and len(line) == max_line_len:
                    raise ValueError(f'Row {csv_header_rows + 1} is too long')
                if line[0].isdigit():
                    # First row with data, test comma delimiter
                    if len(line.split(',')) >= min_columns:
                        csv_delimiter = ','
                    break
                csv_header_rows += 1

        raw_data = np.genfromtxt(self.csv_file, delimiter=csv_delimiter,
                                 dtype=float, skip_header=csv_header_rows)

        if raw_data.shape[0] <= 0:
            raise ValueError('No valid data found')
        if raw_data.shape[1] < min_columns:
            raise ValueError(f'Insufficient number of columns for selected format,'
                             f'required min. {min_columns}, found {raw_data.shape[1]}')

        self._raw_data = np.empty((raw_data.shape[0], 8))
        self._raw_data.fill(np.nan)
        self._raw_data[:, 0] = raw_data[:, id_frame]
        self._raw_data[:, 1] = raw_data[:, id_x] / scale_xy
        self._raw_data[:, 2] = raw_data[:, id_y] / scale_xy
        self._raw_data[:, 3] = raw_data[:, id_sigma_x] / scale_xy
        self._raw_data[:, 4] = raw_data[:, id_sigma_y] / scale_xy
        self._raw_data[:, 5] = raw_data[:, id_intensity]
        self._raw_data[:, 6] = raw_data[:, id_background]
        self._raw_data[:, 7] = raw_data[:, id_precision] / scale_pr

        self.data = self._raw_data.copy()

    def scale_peakfit_data(self,
                           pixel_size: float
                           ) -> None:
        """Scales the raw X,Y coordinates and sigmas to microns.

        The scaling is done for `PEAKFIT` file format only.
        It is a no-op for other formats.

        The scale is applied to original raw data, thus it reverts any
        previously set scale.

        Args:
            pixel_size (float): A pixel size in sample space (in microns).
        """

        if self.file_format == LocalisationFile.Format.PEAKFIT:
            if self.pixel_size != pixel_size:
                self.pixel_size = pixel_size
                # Apply new scale to X,Y coordinates and sigmas
                self.data[:, 1:5] = self._raw_data[:, 1:5] * self.pixel_size

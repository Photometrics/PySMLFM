import warnings
from enum import Enum, unique
from typing import Tuple

import numpy as np
import numpy.typing as npt
from sklearn.neighbors import NearestNeighbors

from .fourier_microscope import FourierMicroscope
from .micro_lens_array import MicroLensArray


class Localisations:
    """A class containing light field localisation data.

    Attributes:
        locs_2d (npt.NDArray[float]): A localisation data in rows, where each
            has 13 columns in this order:

            * [0] frame number (int)
            * [1] U coordinate (in normalised pupil coordinates)
            * [2] V coordinate (in normalised pupil coordinates)
            * [3] X coordinate (in microns)
            * [4] Y coordinate (in microns)
            * [5] sigma X (in microns)
            * [6] sigma Y (in microns)
            * [7] intensity (in photons)
            * [8] background intensity (in photons)
            * [9] precision or uncertainty (in microns)
            * [10] alpha U (in normalised pupil coordinates)
            * [11] alpha V (in normalised pupil coordinates)
            * [12] lens index (int)

        filtered_locs_2d (npt.NDArray[float]):
            A filtered localisations from `locs_2d` attribute.
        min_frame (int): The smallest frame number in the data.
        max_frame (int): The largest frame number in the data.
    """

    @unique
    class AlphaModel(Enum):
        LINEAR = 1
        SPHERE = 2
        INTEGRATE_SPHERE = 3

    def __init__(self,
                 locs_2d_csv: npt.NDArray[float],
                 ):
        """Constructs light field localisation data object.

        Args:
            locs_2d_csv (npt.NDArray[float]):
                A localisation data read from localisation file.
        """

        self.min_frame = int(np.min(locs_2d_csv[:, 0]))
        self.max_frame = int(np.max(locs_2d_csv[:, 0]))

        self.locs_2d = np.zeros((locs_2d_csv.shape[0], 13))

        self.locs_2d[:, 0] = locs_2d_csv[:, 0].copy()
        self.locs_2d[:, 3:10] = locs_2d_csv[:, 1:8].copy()
        # The locs_2d columns 1, 2, 12 are initialized in init_uv()
        # The locs_2d columns 10, 11 are initialized in set_alpha_uv()

        self.filtered_locs_2d = None
        self.reset_filtered_locs()

    def __getattr__(self, name: str):
        return self.__dict__[f"_{name}"]

    def assign_to_lenses(self,
                         mla: MicroLensArray,
                         lfm: FourierMicroscope
                         ) -> None:
        """Initialize U,V values from X,Y mapped to MLA lenses.

        Args:
            mla (MicroLensArray): An instance of micro-lens array class.
            lfm (FourierMicroscope):
                An instance of fourier light field microscope class.
        """

        xy = self.locs_2d[:, 3:5].copy()
        xy *= lfm.xy_to_uv_scale

        lens_centres = mla.lens_centres.copy()
        lens_centres -= mla.centre
        lens_centres *= lfm.mla_to_uv_scale

        knn = NearestNeighbors(n_neighbors=1).fit(lens_centres)
        lens_indices = knn.kneighbors(xy, return_distance=False)

        self.locs_2d[:, 1:3] = lens_centres[lens_indices, :][:, 0, :]  # U, V
        self.locs_2d[:, 12] = lens_indices[:, 0]

    def _filter(self,
                filter_range: Tuple[float, float],
                column_data: npt.NDArray[float]
                ) -> None:
        sel = np.logical_or(column_data < filter_range[0],
                            column_data > filter_range[1])
        self.filtered_locs_2d = self.filtered_locs_2d[~sel, :]

    def reset_filtered_locs(self) -> None:
        self.filtered_locs_2d = self.locs_2d

    def filter_rhos(self,
                    filter_range: Tuple[float, float]
                    ) -> None:
        u = self.filtered_locs_2d[:, 1]
        v = self.filtered_locs_2d[:, 2]
        rho = np.sqrt(u**2 + v**2)
        self._filter(filter_range, rho)

    def filter_spot_sizes(self,
                          filter_range: Tuple[float, float]
                          ) -> None:
        spot_sizes = self.filtered_locs_2d[:, 5]
        self._filter(filter_range, spot_sizes)

    def filter_photons(self,
                       filter_range: Tuple[float, float]
                       ) -> None:
        photons = self.filtered_locs_2d[:, 7]
        self._filter(filter_range, photons)

    def correct_xy(self,
                   correction: npt.NDArray[float]
                   ) -> None:
        # These variables are not modified, no need to copy the data
        u = self.filtered_locs_2d[:, 1]
        v = self.filtered_locs_2d[:, 2]
        # Through these variables are modified the original data
        x = self.filtered_locs_2d[:, 3]
        y = self.filtered_locs_2d[:, 4]

        for i in range(correction.shape[0]):
            idx = np.logical_and(u == correction[i, 0], v == correction[i, 1])
            x[idx] -= correction[i, 2]
            y[idx] -= correction[i, 3]

    def init_alpha_uv(self,
                      model: AlphaModel,
                      lfm: FourierMicroscope
                      ) -> None:
        """TODO: Add documentation.

        Args:
            model (AlphaModel): A model used for mapping.
            lfm (FourierMicroscope):
                An instance of fourier light field microscope class.
        """

        u = self.filtered_locs_2d[:, 1]
        v = self.filtered_locs_2d[:, 2]
        na = lfm.num_aperture
        n = lfm.ref_idx_medium

        if model == Localisations.AlphaModel.LINEAR:
            alpha_u = u.copy()
            alpha_v = v.copy()

        elif model == Localisations.AlphaModel.SPHERE:
            rho = np.sqrt(u**2 + v**2)
            dr_sq = 1 - rho * (na / n)**2  # TODO: REVIEW! Should we use (rho**2) here?
            dr_sq[dr_sq < 0.0] = np.nan  # No negative numbers for sqrt
            phi = -(na / n) / np.sqrt(dr_sq)
            alpha_u = u * phi
            alpha_v = v * phi

        elif model == Localisations.AlphaModel.INTEGRATE_SPHERE:
            u_scaling = lfm.mla_to_uv_scale
            alpha_u, alpha_v = self._phase_average_sphere(
                u, v, u_scaling, na, n, 10)

        else:
            raise ValueError(f'Unsupported alpha model with value {model}')

        self.filtered_locs_2d[:, 10] = alpha_u
        self.filtered_locs_2d[:, 11] = alpha_v

    @staticmethod
    def _phase_average_sphere(u: npt.NDArray[float],
                              v: npt.NDArray[float],
                              u_scaling: float,
                              na: float,
                              n: float,
                              m: int
                              ) -> (npt.NDArray[float], npt.NDArray[float]):
        """TODO: Add documentation."""

        dus2 = u_scaling / 2
        alpha_u = u.copy()
        alpha_v = v.copy()

        for i in range(u.shape[0]):
            range_u = np.linspace(u[i] - dus2, u[i] + dus2, m + 1)
            range_v = np.linspace(v[i] - dus2, v[i] + dus2, m + 1)
            um, vm = np.meshgrid(range_u, range_v)

            rho_sq = um**2 + vm**2
            dr_sq = 1 - rho_sq * (na / n)**2
            dr_sq[dr_sq < 0.0] = np.nan  # No negative numbers for sqrt
            phi = -(na / n) / np.sqrt(dr_sq)

            # Suppress RuntimeWarnings if all values in um/vm are NaNs
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", category=RuntimeWarning)
                alpha_u[i] = np.nanmean(um * phi)
                alpha_v[i] = np.nanmean(vm * phi)

        return alpha_u, alpha_v

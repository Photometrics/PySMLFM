import multiprocessing as mp
import warnings
from enum import Enum, unique
from multiprocessing.shared_memory import SharedMemory as mp_SharedMemory
from typing import Optional, Tuple

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

        min_frame (int): The smallest frame number in the data.
        max_frame (int): The largest frame number in the data.
        filtered_locs_2d (npt.NDArray[float] or None):
            A filtered localisations from `locs_2d` attribute,
            or None if not set via `init_alpha_uv()` function yet.
        alpha_model (AlphaModel or None):
            A model used for mapping,
            or None if not set via `init_alpha_uv()` function yet.
        corrected_locs_2d (npt.NDArray[float] or None):
            A corrected localisations from `filtered_locs_2d` attribute,
            or None if not set via `correct_xy()` function yet.
        correction (npt.NDArray[float] or None):
            An average fit error across all fitted points (in microns),
            or None if not set via `correct_xy()` function yet.
    """

    @unique
    class AlphaModel(Enum):
        LINEAR = 1
        SPHERE = 2
        INTEGRATE_SPHERE = 3

    def __init__(self,
                 locs_2d_csv: npt.NDArray[float]
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
        # The locs_2d columns 1, 2, 12 are initialized in assign_to_lenses()
        # The locs_2d columns 10, 11 remain zeroed
        # The filtered_locs_2d columns 10, 11 are initialized in init_alpha_uv()

        self.filtered_locs_2d: Optional[npt.NDArray[float]] = None
        self.alpha_model: Optional[Localisations.AlphaModel] = None
        self.corrected_locs_2d: Optional[npt.NDArray[float]] = None
        self.correction: Optional[npt.NDArray[float]] = None

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

        lens_centres = mla.lens_centres - mla.centre
        lens_centres *= lfm.mla_to_uv_scale

        knn = NearestNeighbors(n_neighbors=1).fit(lens_centres)
        lens_indices = knn.kneighbors(xy, return_distance=False)

        self.locs_2d[:, 1:3] = lens_centres[lens_indices, :][:, 0, :]  # U, V
        self.locs_2d[:, 12] = lens_indices[:, 0]

        self.reset_filtered_locs()

    def _filter(self,
                filter_range: Tuple[float, float],
                column_data: npt.NDArray[float]
                ) -> None:
        sel = np.logical_or(column_data < filter_range[0],
                            column_data > filter_range[1])
        self.filtered_locs_2d = self.filtered_locs_2d[~sel, :]

    def reset_filtered_locs(self) -> None:
        self.filtered_locs_2d = self.locs_2d.copy()
        self.alpha_model = None
        self.reset_correction()

    def filter_lenses(self,
                      mla: MicroLensArray,
                      lfm: FourierMicroscope
                      ) -> None:
        radius = lfm.bfp_radius / mla.lens_pitch
        radius_sq = radius ** 2
        centres = mla.lens_centres - mla.centre
        distance_sq = np.sum(centres ** 2, axis=1)
        lens_indices = np.nonzero(distance_sq < radius_sq)[0]

        index = self.filtered_locs_2d[:, 12]
        sel = np.any(index[:, None] == lens_indices, axis=-1)
        self.filtered_locs_2d = self.filtered_locs_2d[sel, :]

    def filter_rhos(self,
                    filter_range: Tuple[float, float]
                    ) -> None:
        uv = self.filtered_locs_2d[:, 1:3]
        rhos = np.sqrt(np.sum(uv ** 2, axis=1))
        self._filter(filter_range, rhos)

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

    def init_alpha_uv(self,
                      model: AlphaModel,
                      lfm: FourierMicroscope,
                      abort_event: Optional[mp.Event] = None,
                      worker_count: int = 0
                      ) -> None:
        """TODO: Add documentation.

        Args:
            model (AlphaModel): A model used for mapping.
            lfm (FourierMicroscope):
                An instance of fourier light field microscope class.
            abort_event (Optional[mp.Event]):
                An event to be periodically checked (without blocking).
                If set, the processing is aborted and function returns.
            worker_count (int):
                It is the number of worker processes to run in parallel.
                If it is 0 or less, the number returned by `os.cpu_count()` is used.
        """

        uv = self.filtered_locs_2d[:, 1:3]
        alpha_uv = self.filtered_locs_2d[:, 10:12]
        na = lfm.num_aperture
        n = lfm.ref_idx_medium

        self.reset_correction()

        if model == Localisations.AlphaModel.LINEAR:
            alpha_uv[:] = uv

        elif model == Localisations.AlphaModel.SPHERE:
            rho = np.sqrt(np.sum(uv**2, axis=1))
            dr_sq = 1 - rho * (na / n)**2  # TODO: REVIEW! Should we use (rho**2) here?
            dr_sq[dr_sq < 0.0] = np.nan  # No negative numbers for sqrt
            phi = -(na / n) / np.sqrt(dr_sq)
            alpha_uv[:] = uv * phi[:, np.newaxis]

        elif model == Localisations.AlphaModel.INTEGRATE_SPHERE:
            uv_scaling = lfm.mla_to_uv_scale
            m = 10
            self._phase_average_sphere(
                uv, uv_scaling, na, n, m, alpha_uv, abort_event, worker_count)
            if abort_event is not None:
                if abort_event.is_set():
                    alpha_uv[:] = 0
                    self.alpha_model = None
                    return

        else:
            raise ValueError(f'Unsupported alpha model with value {model}')

        self.alpha_model = model

    def reset_correction(self) -> None:
        self.corrected_locs_2d = None
        self.correction = None

    def correct_xy(self,
                   correction: npt.NDArray[float]
                   ) -> None:
        self.corrected_locs_2d = self.filtered_locs_2d.copy()
        self.correction = correction.copy()

        # These variables are not modified, no need to copy the data
        u = self.corrected_locs_2d[:, 1]
        v = self.corrected_locs_2d[:, 2]
        # Through these variables are modified the original data
        x = self.corrected_locs_2d[:, 3]
        y = self.corrected_locs_2d[:, 4]

        for i in range(correction.shape[0]):
            idx = np.logical_and(u == correction[i, 0], v == correction[i, 1])
            x[idx] -= correction[i, 2]
            y[idx] -= correction[i, 3]

    _SHM_NAME__PHASE_AVG__UV = 'smlfm-phase_avg_sphere-uv'
    _SHM_NAME__PHASE_AVG__ALPHA_UV = 'smlfm-phase_avg_sphere-alpha_uv'

    @staticmethod
    def _phase_average_sphere(uv: npt.NDArray[float],
                              uv_scaling: float,
                              na: float,
                              n: float,
                              m: int,
                              alpha_uv: npt.NDArray[float],
                              abort_event: Optional[mp.Event] = None,
                              worker_count: int = 0
                              ) -> None:
        """TODO: Add documentation."""

        rows_per_task = 500
        row_count = uv.shape[0]
        task_count = int((row_count + rows_per_task - 1) / rows_per_task)

        if worker_count == 1 or task_count == 1:
            Localisations._phase_average_sphere_fn(
                range(row_count), uv, uv_scaling, na, n, m,
                alpha_uv, abort_event)
            return

        shm_bytes = uv.shape[0] * uv.shape[1] * uv.itemsize

        shm_uv = mp_SharedMemory(
            Localisations._SHM_NAME__PHASE_AVG__UV,
            create=True, size=shm_bytes)
        shm_alpha_uv = mp_SharedMemory(
            Localisations._SHM_NAME__PHASE_AVG__ALPHA_UV,
            create=True, size=shm_bytes)

        uv_data = np.ndarray(
            shape=uv.shape, dtype=float, buffer=shm_uv.buf)
        alpha_uv_data = np.ndarray(
            shape=uv.shape, dtype=float, buffer=shm_alpha_uv.buf)

        # Fill shared memory with input data
        uv_data[:] = uv

        try:
            processes = worker_count if worker_count > 0 else None
            with mp.Pool(processes=processes) as pool:
                procs = [Optional[mp.Process]] * task_count

                for idx in range(task_count):
                    i_range_n = range(rows_per_task * idx,
                                      min(rows_per_task * (idx + 1), row_count))
                    # Cannot pass the `abort_event` to processes, otherwise following
                    # runtime error is raised: "Conditional objects should only be
                    # shared between processes through inheritance"
                    args = (i_range_n, row_count, uv_scaling, na, n, m, None)
                    procs[idx] = pool.apply_async(
                        Localisations._phase_average_sphere_task, args)

                for idx in range(task_count):
                    procs[idx].get()
                    if abort_event is not None:
                        if abort_event.is_set():
                            return

        finally:
            if abort_event is None or not abort_event.is_set():
                # Copy output data to target location
                alpha_uv[:] = alpha_uv_data
            shm_alpha_uv.unlink()
            shm_uv.unlink()

    @staticmethod
    def _phase_average_sphere_task(i_range: range,
                                   uv_rows: int,
                                   uv_scaling: float,
                                   na: float,
                                   n: float,
                                   m: int,
                                   abort_event: Optional[mp.Event] = None
                                   ) -> None:
        shm_uv = mp_SharedMemory(
            Localisations._SHM_NAME__PHASE_AVG__UV)
        shm_alpha_uv = mp_SharedMemory(
            Localisations._SHM_NAME__PHASE_AVG__ALPHA_UV)
        try:
            uv = np.ndarray(
                shape=(uv_rows, 2), dtype=float, buffer=shm_uv.buf)
            alpha_uv = np.ndarray(
                shape=(uv_rows, 2), dtype=float, buffer=shm_alpha_uv.buf)

            Localisations._phase_average_sphere_fn(
                i_range, uv, uv_scaling, na, n, m, alpha_uv, abort_event)
        finally:
            shm_alpha_uv.close()
            shm_uv.close()

    @staticmethod
    def _phase_average_sphere_fn(i_range: range,
                                 uv: npt.NDArray[float],
                                 uv_scaling: float,
                                 na: float,
                                 n: float,
                                 m: int,
                                 alpha_uv: npt.NDArray[float],
                                 abort_event: Optional[mp.Event] = None
                                 ) -> None:
        ds2 = uv_scaling / 2

        for i in i_range:
            if abort_event is not None:
                if abort_event.is_set():
                    return

            range_u = np.linspace(uv[i, 0] - ds2, uv[i, 0] + ds2, m + 1)
            range_v = np.linspace(uv[i, 1] - ds2, uv[i, 1] + ds2, m + 1)
            um, vm = np.meshgrid(range_u, range_v)

            rho_sq = um**2 + vm**2
            dr_sq = 1 - rho_sq * (na / n)**2
            dr_sq[dr_sq < 0.0] = np.nan  # No negative numbers for sqrt
            phi = -(na / n) / np.sqrt(dr_sq)

            # Suppress RuntimeWarnings if all values in um/vm are NaNs
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", category=RuntimeWarning)
                alpha_uv[i, 0] = np.nanmean(um * phi)
                alpha_uv[i, 1] = np.nanmean(vm * phi)

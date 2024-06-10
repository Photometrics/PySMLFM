import dataclasses
import multiprocessing as mp
from dataclasses import dataclass
from typing import Callable, List, Optional, Tuple

import numpy as np
import numpy.typing as npt


class Fitting:
    """TODO: Add documentation."""

    @dataclass
    class FitParams:
        # A min. frame number.
        frame_min: int
        # A max. frame number.
        frame_max: int
        # A limit of possible disparity between adjacent views,
        # from negative to positive value (in microns).
        disparity_max: float
        # A step used for disparity range (in microns).
        disparity_step: float
        # A window to accept points as belonging to a given Z (in microns).
        dist_search: float
        # A tolerance for selecting with angles around relative UV (in degrees).
        angle_tolerance: float
        # A max. distance of the candidate (in microns).
        threshold: float
        # A min. number of views the candidate is seen to count it.
        min_views: int
        # A calibration factor between optical and physical Z.
        z_calib: Optional[float] = None

    @dataclass
    class AberrationParams:
        # A max. standard error in Z to apply correction (in microns).
        axial_window: float
        # A min. number of photons to apply correction.
        photon_threshold: int
        # A min. number of views the candidate is seen to count it.
        min_views: int

    @dataclass
    class FitData:
        # A frame number.
        frame: int
        # Basically X, Y and uncalibrated Z coordinates in 3D space (3 values).
        model: npt.NDArray[float]
        # A points included in the fit in format from Localisations class
        # (13 columns).
        points: npt.NDArray[float]
        # Total number of photons in the fit.
        photon_count: int
        # An estimated standard error of model values (3 values).
        std_err: npt.NDArray[float]

    @staticmethod
    def light_field_fit(locs_2d: npt.NDArray[float],
                        rho_scaling: float,
                        fit_params: FitParams,
                        abort_event: Optional[mp.Event] = None,
                        progress_func: Optional[Callable[[int, int, int], None]] = None,
                        progress_step: int = 1000,
                        worker_count: int = 0
                        ) -> Tuple[npt.NDArray[float], List[FitData]]:
        """TODO: Add documentation.

        Args:
            locs_2d (npt.NDArray[float]):
                A localisation data in format from Localisations class,
                i.e. 13 columns.
            rho_scaling (float):
                A scaling factor to convert microns in image plane to rho.
            fit_params (FitParams):
                A configuration for fit detection.
            abort_event (Optional[mp.Event]):
                An event to be periodically checked (without blocking).
                If set, the processing is aborted and function returns.
            progress_func (Optional[Callable[[int, int, int], None]]):
                A callback function for reporting progress. The function gets
                three arguments. First is a frame number of currently processed
                frame, the second and third are min. and max. frame numbers
                received via `fit_params`.
            progress_step (int):
                Defines how often is the `progress_func` function called, if set.
                The frames are processed in groups of 100 frames which is also
                the lowest value.
            worker_count (int):
                It is the number of worker processes to run in parallel.
                If it is 0 or less, the number returned by `os.cpu_count()` is used.

        Returns:
            Returns a tuple.

            - fitted_points (npt.NDArray[float]):
              Holds the fitted data in 2D array with following 8 columns:

              - [0] model data X (float, in microns)
              - [1] model data Y (float, in microns)
              - [2] model data Z (float, in microns)
              - [3] lateral error, a mean of standard errors on X,Y
                    (float, in microns)
              - [4] axial error, a standard error on Z (float, in microns)
              - [5] number of views in fit (int, but stored as float)
              - [6] number of photons in fit (float)
              - [7] frame number (int, but stored as float)

            - total_fit (List[FitData]):
              Holds the list of FitData objects so that individually chosen
              points can be inspected.
        """

        min_frame = fit_params.frame_min
        max_frame = fit_params.frame_max
        frame_count = max_frame - min_frame + 1

        if min_frame > max_frame:
            raise ValueError(
                f'min. frame nr. ({min_frame}) > max. frame nr. ({max_frame})')

        frames_per_task = 100
        task_count = int((frame_count + frames_per_task - 1) / frames_per_task)

        if worker_count == 1 or task_count == 1:
            return Fitting._light_field_fit_task(
                locs_2d, rho_scaling, fit_params, abort_event)

        fitted_points = np.empty((0, 8))
        total_fit = []  # List of FitData

        frame = min_frame
        progress_next_frame = min_frame + progress_step

        processes = worker_count if worker_count > 0 else None
        with mp.Pool(processes=processes) as pool:
            procs = [Optional[mp.Process]] * task_count

            for idx in range(task_count):
                fit_params_n = dataclasses.replace(
                    fit_params,
                    frame_min=min_frame + frames_per_task * idx,
                    frame_max=min(min_frame + frames_per_task * (idx + 1), max_frame),
                )
                # Cannot pass the `abort_event` to processes, otherwise following
                # runtime error is raised: "Conditional objects should only be
                # shared between processes through inheritance"
                args = (locs_2d, rho_scaling, fit_params_n, None)
                procs[idx] = pool.apply_async(Fitting._light_field_fit_task, args)

            for idx in range(task_count):
                fitted_points_n, total_fit_n = procs[idx].get()

                if abort_event is not None:
                    if abort_event.is_set():
                        return np.empty((0, 8)), []

                fitted_points = np.row_stack((fitted_points, fitted_points_n))
                total_fit += total_fit_n

                if progress_func is not None:
                    frame = min(frame + frames_per_task, max_frame)
                    if frame >= progress_next_frame or frame == max_frame:
                        progress_func(frame, min_frame, max_frame)
                        progress_next_frame += progress_step

        return fitted_points, total_fit

    @staticmethod
    def _light_field_fit_task(locs_2d: npt.NDArray[float],
                              rho_scaling: float,
                              fit_params: FitParams,
                              abort_event: Optional[mp.Event] = None,
                              progress_func: Optional[Callable[[int, int, int], None]] = None,
                              progress_step: int = 1000
                              ) -> Tuple[npt.NDArray[float], List[FitData]]:
        """A task executed multiple times in separate process to speed up."""

        min_frame = fit_params.frame_min
        max_frame = fit_params.frame_max
        min_views = fit_params.min_views
        fit_threshold = fit_params.threshold
        z_calib = fit_params.z_calib

        fitted_points = np.empty((0, 8))
        total_fit = []  # List of FitData

        progress_next_frame = min_frame + progress_step

        for frame in range(min_frame, max_frame + 1):

            if abort_event is not None:
                if abort_event.is_set():
                    return np.empty((0, 8)), []

            if progress_func is not None:
                if frame >= progress_next_frame or frame == max_frame:
                    progress_func(frame, min_frame, max_frame)
                    progress_next_frame += progress_step

            # Sort potential seeds by central view first
            candidates = locs_2d[locs_2d[:, 0] == frame, :].copy()
            u = candidates[:, 1]  # Read-only, no copy needed
            v = candidates[:, 2]  # Read-only, no copy needed
            loc_cen_sel = np.logical_and(np.abs(u) < 0.1, np.abs(v) < 0.1)
            loc_cen = candidates[loc_cen_sel, :].copy()
            loc_out_sel = ~np.logical_and(u == 0.0, v == 0.0)
            loc_out = candidates[loc_out_sel, :].copy()
            # Then descending sort by intensity column
            loc_cen = loc_cen[loc_cen[:, 7].argsort()[::-1]]
            loc_out = loc_out[loc_out[:, 7].argsort()[::-1]]
            candidates = np.row_stack((loc_cen, loc_out))

            # Loop over localisations until a few left
            reps = 0
            while candidates.shape[0] > min_views and reps < 100:
                reps += 1
                seed = candidates[0, :]
                loc_fit, view_count, _ = Fitting._group_localisations(
                    seed, candidates, fit_params, rho_scaling)
                # If there are not enough views, don't fit and move on
                if view_count < min_views:
                    candidates = candidates[1:, :]  # Remove first row, the seed
                    continue

                # Fit to points
                model, std_err, _ = Fitting._get_backward_model(loc_fit, rho_scaling)
                # Calculate error in model
                dist = np.sqrt(np.sum(std_err**2))
                # If the final fit distance is too big, don't fit and move on
                if dist > fit_threshold:
                    candidates = candidates[1:, :]  # Remove first row, the seed
                    continue

                # If dist threshold met, remove fitted localisations from candidates
                candidates_sel = np.all(candidates[:, None] == loc_fit, axis=-1).any(-1)
                candidates = candidates[~candidates_sel, :]

                # Add to modelled and fitted points
                if loc_fit.size > 0:
                    photon_count = np.sum(loc_fit[:, 7])
                    new_fit_point = np.array([
                        model[0],  # X
                        model[1],  # Y
                        model[2],  # Z (uncalibrated)
                        np.mean(std_err[0:2]),  # Lateral error
                        std_err[2],  # Axial error
                        view_count + 1,  # Number of views
                        photon_count,  # Number of photons in fit
                        frame  # Frame number
                    ])
                    new_fit_data = Fitting.FitData(
                        frame=frame,
                        model=model,
                        points=loc_fit.copy(),
                        photon_count=photon_count,
                        std_err=std_err,
                    )

                    fitted_points = np.row_stack((fitted_points, new_fit_point))
                    total_fit.append(new_fit_data)

        if z_calib is not None:
            fitted_points[:, 2] *= z_calib

        return fitted_points, total_fit

    @staticmethod
    def calculate_view_error(locs_2d: npt.NDArray[float],
                             rho_scaling: float,
                             fit_data: List[FitData],
                             aberration_params: AberrationParams
                             ) -> npt.NDArray[float]:
        """Calculates average fit error.

        Args:
            locs_2d (npt.NDArray[float]):
                A localisation data in format from Localisations class.
            rho_scaling (float):
                A scaling factor to convert microns in image plane to rho.
            fit_data (List[FitData]):
                A list of FitData objects.
            aberration_params (AberrationParams):
                A configuration for aberration detection.

        Returns:
            Returns average fit error, a sort of average aberration, across all
            fitted points (in microns), with following 5 columns:

            * [0] Original U coordinate (in normalised pupil coordinates)
            * [1] Original V coordinate (in normalised pupil coordinates)
            * [2] Correction of X coordinate (in microns)
            * [3] Correction of Y coordinate (in microns)
            * [4] Number of points used for correction
        """

        min_views = aberration_params.min_views
        photon_threshold = aberration_params.photon_threshold
        axial_window = aberration_params.axial_window
        views = np.unique(locs_2d[:, 1:3], axis=0)  # U,V
        view_count = views.shape[0]
        correction = np.zeros((view_count, 5))
        correction[:, 0:2] = views  # U,V
        for fd in fit_data:
            model = fd.model
            points = fd.points
            photon_count = fd.photon_count
            fit_err = Fitting._get_forward_model_error(model, points, rho_scaling)
            if (points.shape[0] > min_views
                    and np.abs(model[2]) < axial_window
                    and photon_count > photon_threshold):
                for j in range(view_count):
                    dum = fit_err[np.logical_and(
                        points[:, 1] == views[j, 0],
                        points[:, 2] == views[j, 1]), :]
                    if dum.size > 0:
                        correction[j, 2:4] += dum[0]  # Only one match at a time
                        correction[j, 4] += 1

        # Avoid divisions by zero, store zero results instead
        x = correction[:, 2]
        y = correction[:, 3]
        c = correction[:, 4]
        correction[:, 2] = np.divide(x, c, out=np.zeros_like(x), where=c != 0)
        correction[:, 3] = np.divide(y, c, out=np.zeros_like(y), where=c != 0)

        return correction

    @staticmethod
    def _get_backward_model(locs: npt.NDArray[float],
                            rho_scaling: float
                            ) -> Tuple[npt.NDArray[float], npt.NDArray[float], float]:
        """TODO: Add documentation.

        Args:
            locs (npt.NDArray[float]):
                A localisation data in format from Localisations class.
            rho_scaling (float):
                A scaling factor to convert microns in image plane to rho.

        Returns:
            Returns a tuple of 3 values.

            - model (npt.NDArray[float]): An ordinary least-squares (OLS)
              estimates of the regression coefficients (3 values).
              Basically X, Y and uncalibrated Z coordinates in 3D space.
            - std_err (npt.NDArray[float]): An estimated standard error of model
              values (3 values).
            - mse (float): An estimated standard deviation of the
              regression error (a mean squared error).
        """

        # These variables are not modified, no need to copy locs data
        u = locs[:, 1]
        v = locs[:, 2]
        x = locs[:, 3] - u / rho_scaling
        y = locs[:, 4] - v / rho_scaling
        alpha_u = locs[:, 10]
        alpha_v = locs[:, 11]

        zeros = np.zeros_like(alpha_u)
        ones = np.ones_like(alpha_u)

        a = np.row_stack((
            np.column_stack((ones, zeros, alpha_u)),
            np.column_stack((zeros, ones, alpha_v))))
        b = np.concatenate((x, y))

        model, residuals, rank, _s = np.linalg.lstsq(a, b, rcond=None)
        mse = np.mean(residuals) / (a.shape[0] - rank)
        covariant_matrix = mse * np.linalg.inv(np.dot(a.T, a))
        std_err = np.sqrt(np.diag(covariant_matrix))

        return model, std_err, mse

    @staticmethod
    def _get_forward_model_error(model: npt.NDArray[float],
                                 points: npt.NDArray[float],
                                 rho_scaling: float
                                 ) -> npt.NDArray[float]:
        """TODO: Add documentation.

        Args:
            model (npt.NDArray[float]):
                A model returned from `_get_backward_model` function (3 values).
            points (npt.NDArray[float]):
                A candidates returned from `_group_localisations` function.
            rho_scaling (float):
                A scaling factor to convert microns in image plane to rho.

        Returns:
            TODO: Add documentation.
        """

        # These variables are not modified, no need to copy the data
        uv = points[:, 1:3]
        xy = points[:, 3:5]
        alpha_uv = points[:, 10:12]

        xy0 = model[0:2]
        z = model[2]

        dist = xy - (uv / rho_scaling) - xy0 - (z * alpha_uv)
        return dist

    @staticmethod
    def _group_localisations(seed: npt.NDArray[float],
                             in_points: npt.NDArray[float],
                             fit_params: FitParams,
                             rho_scaling: float
                             ) -> Tuple[npt.NDArray[float], int, int]:
        """TODO: Add documentation.

        Args:
            seed (npt.NDArray[float]):
                A single row from Localisation data array (13 columns).
            in_points (npt.NDArray[float]):
                A multiple rows from Localisation data array (13 columns).
            fit_params (FitParams):
                A configuration for grouping.
            rho_scaling (float):
                A scaling factor to convert microns in image plane to rho.

        Returns:
            Returns a tuple of following 3 values.

            - candidates (npt.NDArray[float]): A subset of input points which
              are candidates for being related to a single point given as
              `seed`, (13 columns).
            - view_count(int): A number of views.
            - duplicate_count(int): A number of duplicates.
        """

        angle_tol = np.deg2rad(fit_params.angle_tolerance)
        max_disparity = fit_params.disparity_max
        dis_tol = fit_params.dist_search
        dz = fit_params.disparity_step

        # Seed values are not modified, copy not needed
        su = seed[1]
        sv = seed[2]
        sx = seed[3]
        sy = seed[4]

        points = in_points.copy()

        # First, remove self view points
        seed_sel = np.logical_and(points[:, 1] == su, points[:, 2] == sv)
        points = points[~seed_sel, :]

        # Disparity from seed and relative U and V
        du = points[:, 1] - su
        dv = points[:, 2] - sv
        dx = points[:, 3] - sx
        dy = points[:, 4] - sy

        # Angle selection is relative to the UV index of the seed
        # and dx dy on camera pixels.
        angles_uv = np.arctan2(dv, du)
        angles_xy = np.arctan2(dy, dx)
        angle_sel = np.logical_or(
            np.abs(angles_xy - angles_uv) < angle_tol,
            np.abs(angles_xy - angles_uv) > (np.pi - angle_tol))
        points = points[angle_sel, :]

        # ortho_dist = r * np.sin(np.abs(angles_xy - angles_uv))
        # rect_sel = np.abs(ortho_dist) < dis_tol
        # points = points[~rect_sel, :]

        # Select against relative disparity
        du = points[:, 1] - su
        dv = points[:, 2] - sv
        dx = points[:, 3] - sx
        dy = points[:, 4] - sy
        dxy = np.sqrt(dx**2 + dy**2)
        duv = np.sqrt(du**2 + dv**2)  # Rho
        disparity = (dxy - duv / rho_scaling) / duv

        range_z = np.arange(-max_disparity, max_disparity + dz / 2, dz)
        num_points = np.zeros((range_z.size, 1))
        # The num_points will be in integration of the number of points in
        # each disparity gradient range.
        for z_i in range(range_z.size):
            disparity_sel = np.logical_and(
                disparity > (range_z[z_i] - dis_tol),
                disparity <= (range_z[z_i] + dis_tol))
            num_points[z_i] = np.sum(disparity_sel)
        best_z_i = np.argmax(num_points)
        best_z = range_z[best_z_i]
        # Apply Z-selection
        z_sel = np.logical_or(
            disparity <= (best_z - dis_tol),
            disparity > (best_z + dis_tol))
        points = points[~z_sel, :]

        # Get rid of multiple points in single views.
        # This section looks for multiple localisation within a single view
        # that made the selection - we only need one so pick one.
        # This could be done better, I'm sure!
        # I take the one which has best fit. (not all possible combinations
        # checked though, just as they are found).

        # Initialise set of localisations to fit with the seed being used first
        candidates = seed
        view_count = 0
        duplicate_count = 0
        if points.size > 0:
            uv, uv_i, uv_c = np.unique(points[:, 1:3], axis=0,
                                       return_inverse=True, return_counts=True)
            # Generates indices for localisations belonging to a view
            indices = list([])
            for value in uv:
                indices.append(np.where(np.all(points[:, 1:3] == value, axis=1))[0])
            # Add unique points to candidates
            candidates = np.row_stack(
                (candidates, points[np.isin(uv_i, np.nonzero(uv_c == 1))]))
            # Remove indices with uv_c == 1
            indices = [i for i in indices if len(i) > 1]

            view_count = len(uv_c)
            duplicate_count = len(indices)

            # If there is more than one point in a view,
            # take the one which fits the unique points best
            for i in range(duplicate_count):
                view_ind = indices[i]
                j_count = view_ind.shape[0]
                d = np.zeros((j_count, 1))
                for j in range(j_count):
                    locs = np.row_stack((candidates, points[view_ind[j], :]))
                    std_err = Fitting._get_backward_model(locs, rho_scaling)[1]
                    d[j] = np.sqrt(np.sum(std_err**2))
                d_min_j = np.argmin(d)
                candidates = np.row_stack((candidates, points[view_ind[d_min_j], :]))

            # If there are 2 views that share common U or V, reject the grouping
            var_u = np.var(candidates[:, 1], axis=0, ddof=1)
            var_v = np.var(candidates[:, 2], axis=0, ddof=1)
            if view_count == 1 and (var_u < 0.1 or var_v < 0.1):
                candidates = np.array([])
                view_count = 0

        return candidates, view_count, duplicate_count

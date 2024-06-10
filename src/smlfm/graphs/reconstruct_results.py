from pathlib import Path, PurePath
from typing import Optional, Tuple, Union

import numpy as np
import numpy.typing as npt
from matplotlib.figure import Figure

from ..graphs import draw_3d_locs, draw_occurrences, draw_histogram


def reconstruct_results(fig1: Figure, fig2: Figure, fig3: Figure,
                        locs3d_data_or_file: Union[Path, npt.NDArray[float]],
                        max_lateral_err: Optional[float] = None,
                        min_view_count: Optional[int] = None
                        ) -> Tuple[Figure, Figure, Figure]:
    """Generates 3 final figures with results from stored 3D localisations.

    Args:
        fig3 (Figure): A figure for occurrences.
        fig2 (Figure): A figure for histogram.
        fig1 (Figure): A figure for 3D view.
        locs3d_data_or_file (Path or npt.NDArray[float]):
            A CSV file path or a numpy array with 3D localisations.
        max_lateral_err (Optional[float]):
            Max. lateral error to show (in microns).
        min_view_count(Optional[int]):
            Shown only points with given min. number of views.

    Returns:
        Returns a tuple with 3 figures: occurrences, histogram and 3D view.
    """

    if isinstance(locs3d_data_or_file, np.ndarray):
        locs_3d = locs3d_data_or_file
    elif isinstance(locs3d_data_or_file, PurePath):
        locs_3d = np.genfromtxt(locs3d_data_or_file, delimiter=',', dtype=float)
    else:
        raise TypeError('Unsupported argument type with 3D localisations')

    xyz = locs_3d[:, 0:3]  # X, Y, Z
    lateral_err = locs_3d[:, 3]  # Fitting error in X and Y (in microns)
    axial_err = locs_3d[:, 4]  # Fitting error in Z (in microns)
    view_count = locs_3d[:, 5]  # Number of views used to fit the localisation
    photons = locs_3d[:, 6]  # Number of photons in fit
    # frames = locs_3d[:, 7]  # Frames

    keep = np.logical_and(
        (lateral_err < max_lateral_err) if max_lateral_err is not None else True,
        (view_count > min_view_count) if min_view_count is not None else True)

    draw_occurrences(fig1, lateral_err[keep], axial_err[keep], photons[keep])
    draw_histogram(fig2, photons[keep], axial_err[keep])
    draw_3d_locs(fig3, xyz[keep])

    return fig1, fig2, fig3

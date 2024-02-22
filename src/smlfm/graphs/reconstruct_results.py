from pathlib import Path, PurePath
from typing import Tuple, Union

import numpy as np
import numpy.typing as npt
from matplotlib import pyplot as plt

from ..graphs import add_watermark, draw_3d_locs, draw_occurrences, draw_histogram


def reconstruct_results(locs3d_data_or_file: Union[Path, npt.NDArray[float]],
                        max_lateral_err: Union[float, None] = None,
                        min_view_count: Union[int, None] = None
                        ) -> Tuple[plt.Figure, plt.Figure, plt.Figure]:
    """Generates 3 final figures with results from stored 3D localisations.

    Args:
        locs3d_data_or_file (Path or npt.NDArray[float]):
            A CSV file path or a numpy array with 3D localisations.
        max_lateral_err (float): Max. lateral error to show (in microns).
        min_view_count(int): Shown only points with given min. number of views.

    Returns:
        Returns a tuple with 3 figures: occurrences, histogram and 3D view.
    """

    if isinstance(locs3d_data_or_file, np.ndarray):
        locs_3d = locs3d_data_or_file
    elif isinstance(locs3d_data_or_file, PurePath):
        locs_3d = np.genfromtxt(locs3d_data_or_file, delimiter=',', dtype=float)
    else:
        raise TypeError(f'Unsupported argument type with 3D localisations')

    xyz = locs_3d[:, 0:3]  # X, Y, Z
    lateral_err = locs_3d[:, 3]  # Fitting error in X and Y (in microns)
    axial_err = locs_3d[:, 4]  # Fitting error in Z (in microns)
    view_count = locs_3d[:, 5]  # Number of views used to fit the localization
    photons = locs_3d[:, 6]  # Number of photons in fit
    # frames = locs_3d[:, 7]  # Frames

    keep = np.logical_and(
        (lateral_err < max_lateral_err) if max_lateral_err is not None else True,
        (view_count > min_view_count) if min_view_count is not None else True)

    fig1 = draw_occurrences(lateral_err[keep], axial_err[keep], photons[keep])
    fig2 = draw_histogram(photons[keep], axial_err[keep])
    fig3 = draw_3d_locs(xyz[keep])

    return fig1, fig2, fig3

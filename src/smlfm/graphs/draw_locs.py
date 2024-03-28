from typing import Union

import numpy as np
import numpy.typing as npt
from matplotlib import cm
from matplotlib import colors
from matplotlib.axes import Axes
from matplotlib.colorbar import Colorbar
from matplotlib.figure import Figure

from ..graphs import add_watermark


def draw_locs(fig: Figure,
              xy: npt.NDArray[float],
              lens_idx: npt.NDArray[float],
              lens_centres: Union[npt.NDArray[float], None] = None,
              mla_centre: Union[npt.NDArray[float], None] = None
              ) -> Figure:
    fig.clear(True)
    fig.set_size_inches(6, 5)
    fig.set_layout_engine('tight')

    ax: Axes = fig.add_subplot()
    ax.set_xlabel(r'X [$\mu$m]')
    ax.set_ylabel(r'Y [$\mu$m]')

    ax.scatter(xy[:, 0], xy[:, 1], s=1, c=lens_idx, marker='.')

    lens_idx_uni = np.unique(lens_idx).astype(int)

    if lens_centres is not None:
        lens_centres_uni = lens_centres[lens_idx_uni, :]
        ax.scatter(lens_centres_uni[:, 0], lens_centres_uni[:, 1],
                   s=3, c='tomato')

    if mla_centre is not None:
        ax.scatter(mla_centre[0], mla_centre[1],
                   s=20, c='red', marker='x')

    cbar_lenses = lens_idx_uni
    cbar_labels = [str(i) for i in cbar_lenses]
    cbar_bounds = np.concatenate((cbar_lenses, [cbar_lenses[-1] + 1])) - 0.5
    cbar_ticks = (cbar_bounds[1:] + cbar_bounds[:-1]) / 2
    cbar_norm = colors.BoundaryNorm(boundaries=cbar_bounds, ncolors=256)
    cbar: Colorbar = fig.colorbar(
        cm.ScalarMappable(norm=cbar_norm), ax=ax,
        boundaries=cbar_bounds, values=cbar_lenses)
    cbar.ax.tick_params(which='both', size=0)  # Hide ticks
    cbar.set_ticks(cbar_ticks.tolist(), labels=cbar_labels)
    cbar.set_label('Lens index')

    if lens_centres is not None:
        for i in lens_idx_uni:
            ax.annotate(str(i),
                        xy=(lens_centres[i, 0], lens_centres[i, 1]),
                        xycoords='data',
                        xytext=(1.5, 1.0),
                        alpha=0.5,
                        textcoords='offset points',
                        size=10)

    ax.set_aspect('equal')
    add_watermark(fig)
    return fig
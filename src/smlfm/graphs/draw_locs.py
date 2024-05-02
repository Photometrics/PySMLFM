from typing import Optional

import numpy as np
import numpy.typing as npt
from matplotlib import cm
from matplotlib import colors
from matplotlib.axes import Axes
from matplotlib.colorbar import Colorbar
from matplotlib.figure import Figure
from matplotlib.patches import Circle

from ..graphs import add_watermark


def draw_locs(fig: Figure,
              xy: npt.NDArray[float],
              lens_idx: npt.NDArray[float],
              lens_centres: Optional[npt.NDArray[float]] = None,
              mla_centre: Optional[npt.NDArray[float]] = None,
              bfp_radius: Optional[float] = None,
              set_default_size: bool = True
              ) -> Figure:
    fig.clear(True)
    if set_default_size:
        fig.set_size_inches(6, 5)
    fig.set_layout_engine('tight')

    ax: Axes = fig.add_subplot()
    ax.set_xlabel(r'X [$\mu$m]')
    ax.set_ylabel(r'Y [$\mu$m]')

    lens_idx_uni = np.unique(lens_idx).astype(int)

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

    if bfp_radius is not None and mla_centre is not None:
        bfp = Circle(xy=(float(mla_centre[0]), float(mla_centre[1])),
                     radius=bfp_radius, fill=False,
                     edgecolor='purple', alpha=0.25)
        ax.add_patch(bfp)

    ax.scatter(xy[:, 0], xy[:, 1], s=1, c=lens_idx, marker=',', lw=0)

    if mla_centre is not None:
        ax.scatter(mla_centre[0], mla_centre[1],
                   s=20, c='red', marker='x')

    if lens_centres is not None:
        lens_centres_uni = lens_centres[lens_idx_uni, :]
        ax.scatter(lens_centres_uni[:, 0], lens_centres_uni[:, 1],
                   s=3, c='tomato')
        for i in lens_idx_uni:
            ax.annotate(str(i),
                        xy=(lens_centres[i, 0], lens_centres[i, 1]),
                        xycoords='data',
                        xytext=(5.0, 2.5),
                        alpha=0.75,
                        textcoords='offset points',
                        size=10)

    ax.set_aspect('equal')
    add_watermark(fig)
    return fig

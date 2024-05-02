from typing import Optional

import numpy.typing as npt
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from ..graphs import add_watermark


def draw_locs_normalised(fig: Figure,
                         xy: npt.NDArray[float],
                         uv: npt.NDArray[float],
                         lens_idx: npt.NDArray[float],
                         mla_centre: Optional[npt.NDArray[float]] = None,
                         set_default_size: bool = True
                         ) -> Figure:
    fig.clear(True)
    if set_default_size:
        fig.set_size_inches(5, 5)
    fig.set_layout_engine('tight')

    ax: Axes = fig.add_subplot()
    ax.set_xticks([])
    ax.set_yticks([])

    ax.scatter(xy[:, 0], xy[:, 1],
               s=1, c=lens_idx, marker=',', lw=0)

    ax.scatter(uv[:, 0], uv[:, 1],
               s=3, c='tomato')

    if mla_centre is not None:
        ax.scatter(mla_centre[0], mla_centre[1],
                   s=20, c='red', marker='x')

    ax.set_aspect('equal')
    add_watermark(fig)
    return fig

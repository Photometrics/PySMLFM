from typing import Optional

import numpy.typing as npt
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from ..graphs import add_watermark


def draw_mla(fig: Figure,
             lens_centres: npt.NDArray[float],
             mla_centre: Optional[npt.NDArray[float]] = None,
             set_default_size: bool = True
             ) -> Figure:
    fig.clear(True)
    if set_default_size:
        fig.set_size_inches(5, 5)
    fig.set_layout_engine('tight')

    ax: Axes = fig.add_subplot()
    ax.scatter(lens_centres[:, 0], lens_centres[:, 1],
               s=3, c='tomato', marker='o')

    if mla_centre is not None:
        ax.scatter(mla_centre[0], mla_centre[1],
                   s=20, c='red', marker='x')

    for i in range(lens_centres.shape[0]):
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

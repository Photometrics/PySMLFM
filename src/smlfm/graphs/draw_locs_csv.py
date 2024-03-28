import numpy.typing as npt
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from ..graphs import add_watermark


def draw_locs_csv(fig: Figure, locs: npt.NDArray[float]) -> Figure:
    fig.clear(True)
    fig.set_size_inches(5, 5)
    fig.set_layout_engine('tight')

    ax: Axes = fig.add_subplot()
    ax.scatter(locs[:, 0], locs[:, 1],
               s=1, c='green', marker='.')

    ax.set_aspect('equal')
    add_watermark(fig)
    return fig

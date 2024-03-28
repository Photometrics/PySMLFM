import numpy.typing as npt
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from ..graphs import add_watermark


def draw_histogram(fig: Figure,
                   photons: npt.NDArray[float],
                   axial_err: npt.NDArray[float],
                   ) -> Figure:
    fig.clear(True)
    fig.set_size_inches(6, 5)
    fig.set_layout_engine('tight')

    ax: Axes = fig.add_subplot()
    ax.set_xlabel('Photons')
    ax.set_ylabel('Axial precision [nm]')
    gr = ax.hist2d(photons, axial_err * 1000, bins=40)

    fig.colorbar(gr[3], ax=ax)

    add_watermark(fig)
    return fig
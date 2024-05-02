import numpy.typing as npt
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from ..graphs import add_watermark


def draw_histogram(fig: Figure,
                   photons: npt.NDArray[float],
                   axial_err: npt.NDArray[float],
                   bins: int = 40,
                   set_default_size: bool = True
                   ) -> Figure:
    fig.clear(True)
    if set_default_size:
        fig.set_size_inches(6, 5)
    fig.set_layout_engine('tight')

    ax: Axes = fig.add_subplot()
    ax.set_xlabel('Photons')
    ax.set_ylabel('Axial precision [nm]')
    gr = ax.hist2d(photons, axial_err * 1000, bins=bins)

    cbar = fig.colorbar(gr[3], ax=ax)
    cbar.set_label('Number of localisations')

    add_watermark(fig)
    return fig

import numpy.typing as npt
from matplotlib.figure import Figure

from ..graphs import add_watermark


def draw_occurrences(fig: Figure,
                     lateral_err: npt.NDArray[float],
                     axial_err: npt.NDArray[float],
                     photons: npt.NDArray[float],
                     ) -> Figure:
    fig.clear(True)
    fig.set_size_inches(15, 5)
    fig.set_layout_engine('tight')

    ax0, ax1, ax2 = fig.subplots(ncols=3)
    ax0.set_xlabel('Lateral fit error [nm]')
    ax0.set_ylabel('Occurrence')
    ax0.hist(lateral_err * 1000, bins=40)

    ax1.set_xlabel('Axial fit error [nm]')
    ax1.set_ylabel('Occurrence')
    ax1.hist(axial_err * 1000, bins=40)

    ax2.set_xlabel('Number of photons')
    ax2.set_ylabel('Occurrence')
    ax2.hist(photons, bins=40)

    add_watermark(fig)
    return fig

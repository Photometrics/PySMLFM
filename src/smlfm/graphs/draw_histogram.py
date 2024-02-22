import numpy.typing as npt
from matplotlib import pyplot as plt

from ..graphs import add_watermark


def draw_histogram(photons: npt.NDArray[float],
                   axial_err: npt.NDArray[float],
                   title: str = 'Histogram'
                   ) -> plt.Figure:
    fig = plt.figure(figsize=(6, 5), layout='tight')
    fig.canvas.manager.set_window_title(title)

    ax = fig.add_subplot()
    ax.set_xlabel('Photons')
    ax.set_ylabel('Axial precision [nm]')
    gr = ax.hist2d(photons, axial_err * 1000, bins=40)

    fig.colorbar(gr[3], ax=ax)

    add_watermark(fig)
    return fig

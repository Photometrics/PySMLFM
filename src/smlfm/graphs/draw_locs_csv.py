import numpy.typing as npt
from matplotlib import pyplot as plt

from ..graphs import add_watermark


def draw_locs_csv(locs: npt.NDArray[float],
                  title: str = 'Localisations centered around means'
                  ) -> plt.Figure:
    fig = plt.figure(figsize=(5, 5), layout='tight')
    fig.canvas.manager.set_window_title(title)

    ax = fig.add_subplot()
    ax.scatter(locs[:, 0], locs[:, 1],
               s=1, c='green', marker='.')

    ax.set_aspect('equal')
    add_watermark(fig)
    return fig

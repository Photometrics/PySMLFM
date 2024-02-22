import numpy.typing as npt
from matplotlib import pyplot as plt

from ..graphs import add_watermark


def draw_3d_locs(xyz: npt.NDArray[float],
                 title: str = '3D'
                 ) -> plt.Figure:
    # fig = plt.figure(figsize=(5, 5))  # No layout='tight'
    fig = plt.figure(figsize=(5, 5), layout='tight')
    fig.canvas.manager.set_window_title(title)

    ax = fig.add_subplot(projection='3d')
    ax.set_xlabel(r'X [$\mu$m]')
    ax.set_ylabel(r'Y [$\mu$m]')
    ax.set_zlabel(r'Z [$\mu$m]')
    ax.scatter(xyz[:, 0], xyz[:, 1], xyz[:, 2],
               s=1, c=xyz[:, 2], marker='o')

    # ax.view_init(azim=-75, elev=15)  # Doesn't work with tight layout
    ax.set_aspect('equal')
    add_watermark(fig)
    return fig

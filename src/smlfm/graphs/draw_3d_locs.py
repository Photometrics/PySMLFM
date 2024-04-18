import numpy.typing as npt
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d.axes3d import Axes3D

from ..graphs import add_watermark


def draw_3d_locs(fig: Figure,
                 xyz: npt.NDArray[float],
                 set_default_size: bool = True
                 ) -> Figure:
    fig.clear(True)
    if set_default_size:
        fig.set_size_inches(5, 5)
    fig.set_layout_engine('tight')

    ax: Axes3D = fig.add_subplot(projection='3d')
    ax.set_xlabel(r'X [$\mu$m]')
    ax.set_ylabel(r'Y [$\mu$m]')
    ax.set_zlabel(r'Z [$\mu$m]')
    ax.scatter(xyz[:, 0], xyz[:, 1], xyz[:, 2],
               s=1, c=xyz[:, 2], marker='o')

    # ax.view_init(azim=-75, elev=15)  # Doesn't work with tight layout
    ax.set_aspect('equal')
    add_watermark(fig)
    return fig

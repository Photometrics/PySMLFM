from typing import Union

import numpy.typing as npt
from matplotlib import pyplot as plt

from ..graphs import add_watermark


def draw_locs_normalised(xy: npt.NDArray[float],
                         uv: npt.NDArray[float],
                         lens_idx: npt.NDArray[float],
                         mla_centre: Union[npt.NDArray[float], None] = None,
                         title: str = 'Normalised localisations with lens centers'
                         ) -> plt.Figure:
    fig = plt.figure(figsize=(5, 5), layout='tight')
    fig.canvas.manager.set_window_title(title)

    ax = fig.add_subplot()
    ax.set_xticks([])
    ax.set_yticks([])

    ax.scatter(xy[:, 0], xy[:, 1],
               s=1, c=lens_idx, marker='.')

    ax.scatter(uv[:, 0], uv[:, 1],
               s=3, c='tomato')

    if mla_centre is not None:
        ax.scatter(mla_centre[0], mla_centre[1],
                   s=20, c='red', marker='x')

    ax.set_aspect('equal')
    add_watermark(fig)
    return fig

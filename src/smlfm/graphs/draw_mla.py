from typing import Union

import numpy.typing as npt
from matplotlib import pyplot as plt

from ..graphs import add_watermark


def draw_mla(lens_centres: npt.NDArray[float],
             mla_centre: Union[npt.NDArray[float], None] = None,
             title: str = 'Micro-lens array centres'
             ) -> plt.Figure:
    fig = plt.figure(figsize=(5, 5), layout='tight')
    fig.canvas.manager.set_window_title(title)

    ax = fig.add_subplot()
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
                    textcoords='offset points',
                    size=10)

    ax.set_aspect('equal')
    add_watermark(fig)
    return fig

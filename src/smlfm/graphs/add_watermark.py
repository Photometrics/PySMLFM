import io
import pkgutil

from PIL import Image
from matplotlib import pyplot as plt
from matplotlib.image import FigureImage

from .. import __name__ as _pkg_name_


def add_watermark(fig: plt.Figure) -> FigureImage:
    img_data = pkgutil.get_data(_pkg_name_, 'data/tdy-watermark.png')
    img = Image.open(io.BytesIO(img_data))

    return fig.figimage(img, xo=0, yo=0, zorder=10, alpha=0.25)

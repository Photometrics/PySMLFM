import tkinter as tk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
from matplotlib.figure import Figure


class FigureWindow(tk.Toplevel):

    def __init__(self, figure: Figure, *args, **kwargs):
        title = kwargs.pop('title', None)
        super().__init__(*args, **kwargs)

        if title is not None:
            self.wm_title(title)

        self.figure = figure
        if self.figure.canvas.manager is not None:
            print('WARNING: Tkinter does not like pyplot figures')

        size = self.figure.bbox.size.astype(int)
        self.geometry(f'{size[0]}x{size[1]}')

        self.canvas = FigureCanvasTkAgg(self.figure, master=self)
        self.canvas.draw()

        self.toolbar = NavigationToolbar2Tk(self.canvas, window=self)
        self.toolbar.update()

        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Just hide the window instead of releasing it.
        # Use `destroy()` to release it from memory.
        self.protocol('WM_DELETE_WINDOW', func=self.withdraw)
        self.bind('<Escape>', func=lambda _evt: self.withdraw())

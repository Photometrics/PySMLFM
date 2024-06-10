#!/usr/bin/env python3
import tkinter as tk

from .app_model import AppModel
from .consts import StageType


class App(tk.Tk):
    def __init__(self):
        super().__init__()

        # Remain invisible until the UI is fully constructed
        self.withdraw()

        self._model = AppModel()

        self.title('Single Molecule Light Field Microscopy')
        self.iconphoto(True, self._model.icons.app)

        self._model.create_gui(self)

        # Set default size and position (enlarges to min. size if necessary)
        self.geometry('450x500+0+0')

        # Now it is ready to become visible
        self.deiconify()

        self._model.stage_start_update(StageType.CONFIG)


def app():
    a = App()
    a.mainloop()


if __name__ == '__main__':
    app()

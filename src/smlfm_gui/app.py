#!/usr/bin/env python3
import tkinter as tk

from .app_model import AppModel
from .consts import *


class App(tk.Tk):
    def __init__(self):
        super().__init__()

        self._model = AppModel()

        self.title('Single Molecule Light Field Microscopy')
        self.iconphoto(True, self._model.icons.app)

        self._model.create_gui(self)

        # Set default size (enlarges to min. size if necessary)
        self.geometry('450x500')

        self._model.stage_invalidate(StageType.CONFIG)

        # Load configuration given via CLI option or wait for user to select
        if self._model.cli_cfg_file is not None:
            self._model.stage_start_update(StageType.CONFIG)


def app():
    a = App()
    a.mainloop()


if __name__ == '__main__':
    app()

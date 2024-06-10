import tkinter as tk
from idlelib.tooltip import Hovertip
from tkinter import ttk
from typing import Callable, Optional

import numpy as np

import smlfm
from .app_model import AppModel
from .cfg_dialog import CfgDialog
from .consts import READONLY


class FilterCfgDialog(CfgDialog):

    def __init__(self, parent, model: AppModel, title: Optional[str] = None,
                 process_cb: Optional[Callable[[bool], None]] = None):
        if title is None:
            title = 'Model & Filtering Settings'

        self._ui_filter_lenses: Optional[ttk.Checkbutton] = None
        self._var_filter_lenses = tk.BooleanVar(value=model.cfg.filter_lenses)

        self._ui_filter_rhos: Optional[ttk.Checkbutton] = None
        self._var_filter_rhos = tk.BooleanVar(
            value=model.cfg.filter_rhos is not None)
        self._ui_filter_rhos_min: Optional[ttk.Entry] = None
        self._var_filter_rhos_min = tk.StringVar()
        self._ui_filter_rhos_min_tip: Optional[Hovertip] = None
        self._ui_filter_rhos_max: Optional[ttk.Entry] = None
        self._var_filter_rhos_max = tk.StringVar()
        self._ui_filter_rhos_max_tip: Optional[Hovertip] = None
        if model.cfg.filter_rhos is not None:
            self._var_filter_rhos_min.set(str(model.cfg.filter_rhos[0]))
            self._var_filter_rhos_max.set(str(model.cfg.filter_rhos[1]))

        self._ui_filter_spot_sizes: Optional[ttk.Checkbutton] = None
        self._var_filter_spot_sizes = tk.BooleanVar(
            value=model.cfg.filter_spot_sizes is not None)
        self._ui_filter_spot_sizes_min: Optional[ttk.Entry] = None
        self._var_filter_spot_sizes_min = tk.StringVar()
        self._ui_filter_spot_sizes_min_tip: Optional[Hovertip] = None
        self._ui_filter_spot_sizes_max: Optional[ttk.Entry] = None
        self._var_filter_spot_sizes_max = tk.StringVar()
        self._ui_filter_spot_sizes_max_tip: Optional[Hovertip] = None
        if model.cfg.filter_spot_sizes is not None:
            self._var_filter_spot_sizes_min.set(str(model.cfg.filter_spot_sizes[0]))
            self._var_filter_spot_sizes_max.set(str(model.cfg.filter_spot_sizes[1]))

        self._ui_filter_photons: Optional[ttk.Checkbutton] = None
        self._var_filter_photons = tk.BooleanVar(
            value=model.cfg.filter_photons is not None)
        self._ui_filter_photons_min: Optional[ttk.Entry] = None
        self._var_filter_photons_min = tk.StringVar()
        self._ui_filter_photons_min_tip: Optional[Hovertip] = None
        self._ui_filter_photons_max: Optional[ttk.Entry] = None
        self._var_filter_photons_max = tk.StringVar()
        self._ui_filter_photons_max_tip: Optional[Hovertip] = None
        if model.cfg.filter_photons is not None:
            self._var_filter_photons_min.set(str(model.cfg.filter_photons[0]))
            self._var_filter_photons_max.set(str(model.cfg.filter_photons[1]))

        self._ui_alpha_model: Optional[ttk.Combobox] = None
        self._var_alpha_model = tk.StringVar(value=model.cfg.alpha_model.name)

        super().__init__(parent, model, title, process_cb=process_cb)

    # noinspection PyProtectedMember, PyBroadException
    # pylint: disable=protected-access
    def body(self, master) -> tk.BaseWidget:
        ui_tab = ttk.Frame(master)
        row = 0

        self._ui_filter_lenses = ttk.Checkbutton(
            ui_tab, onvalue=True, offvalue=False,
            text='Filter lenses outside back focal plane',
            variable=self._var_filter_lenses)
        Hovertip(self._ui_filter_lenses, text=self.model.cfg._filter_lenses_doc)
        self.ui_widgets.append(self._ui_filter_lenses)
        #
        self._ui_filter_lenses.grid(column=0, row=row, sticky=tk.EW, columnspan=3)
        row += 1

        try:
            uv = self.model.lfl.locs_2d[:, 1:3]
            rho = np.sqrt(np.sum(uv ** 2, axis=1))
            limits = f'\n\nFor current data MIN={np.min(rho)}, MAX={np.max(rho)}'
        except BaseException:
            limits = ''
        #
        ui_filter_rhos = ttk.Checkbutton(
            ui_tab, onvalue=True, offvalue=False, text='Filter rhos:',
            variable=self._var_filter_rhos,
            command=lambda: self.enable(True))
        Hovertip(ui_filter_rhos,
                 text=self.model.cfg._filter_rhos_doc + limits)
        self.ui_widgets.append(ui_filter_rhos)
        self._ui_filter_rhos_min = ttk.Entry(
            ui_tab, textvariable=self._var_filter_rhos_min)
        self._ui_filter_rhos_min_tip = Hovertip(
            self._ui_filter_rhos_min,
            text=self.model.cfg._filter_rhos_doc + limits)
        self.ui_widgets.append(self._ui_filter_rhos_min)
        self._ui_filter_rhos_max = ttk.Entry(
            ui_tab, textvariable=self._var_filter_rhos_max)
        self._ui_filter_rhos_max_tip = Hovertip(
            self._ui_filter_rhos_max,
            text=self.model.cfg._filter_rhos_doc + limits)
        self.ui_widgets.append(self._ui_filter_rhos_max)
        ui_filter_rhos_unit = ttk.Label(ui_tab, text='[npc]')
        Hovertip(ui_filter_rhos_unit, text='normalised pupil coordinates')
        #
        ui_filter_rhos.grid(column=0, row=row, sticky=tk.EW)
        self._ui_filter_rhos_min.grid(column=1, row=row, sticky=tk.EW)
        self._ui_filter_rhos_max.grid(column=2, row=row, sticky=tk.EW)
        ui_filter_rhos_unit.grid(column=3, row=row, sticky=tk.W)
        row += 1

        try:
            spot_sizes = self.model.lfl.locs_2d[:, 5]
            limits = (f'\n\nFor current data'
                      f' MIN={np.min(spot_sizes)}, MAX={np.max(spot_sizes)}')
        except BaseException:
            limits = ''
        #
        ui_filter_spot_sizes = ttk.Checkbutton(
            ui_tab, onvalue=True, offvalue=False, text='Filter spot sizes:',
            variable=self._var_filter_spot_sizes,
            command=lambda: self.enable(True))
        Hovertip(ui_filter_spot_sizes,
                 text=self.model.cfg._filter_spot_sizes_doc + limits)
        self.ui_widgets.append(ui_filter_spot_sizes)
        self._ui_filter_spot_sizes_min = ttk.Entry(
            ui_tab, textvariable=self._var_filter_spot_sizes_min)
        self._ui_filter_spot_sizes_min_tip = Hovertip(
            self._ui_filter_spot_sizes_min,
            text=self.model.cfg._filter_spot_sizes_doc + limits)
        self.ui_widgets.append(self._ui_filter_spot_sizes_min)
        self._ui_filter_spot_sizes_max = ttk.Entry(
            ui_tab, textvariable=self._var_filter_spot_sizes_max)
        self._ui_filter_spot_sizes_max_tip = Hovertip(
            self._ui_filter_spot_sizes_max,
            text=self.model.cfg._filter_spot_sizes_doc + limits)
        self.ui_widgets.append(self._ui_filter_spot_sizes_max)
        ui_filter_spot_sizes_unit = ttk.Label(ui_tab, text='\u00B5m')  # microns
        #
        ui_filter_spot_sizes.grid(column=0, row=row, sticky=tk.EW)
        self._ui_filter_spot_sizes_min.grid(column=1, row=row, sticky=tk.EW)
        self._ui_filter_spot_sizes_max.grid(column=2, row=row, sticky=tk.EW)
        ui_filter_spot_sizes_unit.grid(column=3, row=row, sticky=tk.W)
        row += 1

        try:
            photons = self.model.lfl.locs_2d[:, 7]
            limits = (f'\n\nFor current data'
                      f' MIN={np.min(photons)}, MAX={np.max(photons)}')
        except BaseException:
            limits = ''
        #
        ui_filter_photons = ttk.Checkbutton(
            ui_tab, onvalue=True, offvalue=False, text='Filter photons:',
            variable=self._var_filter_photons,
            command=lambda: self.enable(True))
        Hovertip(ui_filter_photons,
                 text=self.model.cfg._filter_photons_doc + limits)
        self.ui_widgets.append(ui_filter_photons)
        self._ui_filter_photons_min = ttk.Entry(
            ui_tab, textvariable=self._var_filter_photons_min)
        self._ui_filter_photons_min_tip = Hovertip(
            self._ui_filter_photons_min,
            text=self.model.cfg._filter_photons_doc + limits)
        self.ui_widgets.append(self._ui_filter_photons_min)
        self._ui_filter_photons_max = ttk.Entry(
            ui_tab, textvariable=self._var_filter_photons_max)
        self._ui_filter_photons_max_tip = Hovertip(
            self._ui_filter_photons_max,
            text=self.model.cfg._filter_photons_doc + limits)
        self.ui_widgets.append(self._ui_filter_photons_max)
        ui_filter_photons_unit = ttk.Label(ui_tab, text='photons')
        #
        ui_filter_photons.grid(column=0, row=row, sticky=tk.EW)
        self._ui_filter_photons_min.grid(column=1, row=row, sticky=tk.EW)
        self._ui_filter_photons_max.grid(column=2, row=row, sticky=tk.EW)
        ui_filter_photons_unit.grid(column=3, row=row, sticky=tk.W)
        row += 1

        ui_alpha_model_lbl = ttk.Label(ui_tab, text='Alpha model:')
        Hovertip(ui_alpha_model_lbl, text=self.model.cfg._alpha_model_doc)
        self._ui_alpha_model = ttk.Combobox(
            ui_tab, state=READONLY,
            values=[t.name for t in smlfm.Localisations.AlphaModel],
            textvariable=self._var_alpha_model)
        Hovertip(self._ui_alpha_model, text=self.model.cfg._alpha_model_doc)
        self.ui_widgets.append(self._ui_alpha_model)
        #
        ui_alpha_model_lbl.grid(column=0, row=row, sticky=tk.EW)
        self._ui_alpha_model.grid(column=1, row=row, sticky=tk.EW, columnspan=2)
        row += 1

        # Final padding and layout
        ui_tab.columnconfigure(index=1, weight=1)
        ui_tab.columnconfigure(index=2, weight=1)
        self.model.grid_slaves_configure(ui_tab, padx=1, pady=1)

        ui_tab.pack(anchor=tk.NW, fill=tk.X, expand=True, padx=5, pady=5)

        return self._ui_filter_lenses  # Control that gets initial focus

    # pylint: disable=too-many-return-statements
    # pylint: disable=protected-access
    def validate(self) -> bool:
        if self._var_filter_rhos.get():
            if not self.is_float(self._var_filter_rhos_min.get()):
                self.initial_focus = self._ui_filter_rhos_min
                self._ui_filter_rhos_min_tip.showtip()
                return False
            if not self.is_float(self._var_filter_rhos_max.get()):
                self.initial_focus = self._ui_filter_rhos_max
                self._ui_filter_rhos_max_tip.showtip()
                return False
            rhos_min = float(self._var_filter_rhos_min.get())
            rhos_max = float(self._var_filter_rhos_max.get())
            if rhos_min > rhos_max:
                self.initial_focus = self._ui_filter_rhos_max
                self._ui_filter_rhos_max_tip.showtip()
                return False
        if self._var_filter_spot_sizes.get():
            if not self.is_float(self._var_filter_spot_sizes_min.get()):
                self.initial_focus = self._ui_filter_spot_sizes_min
                self._ui_filter_spot_sizes_min_tip.showtip()
                return False
            if not self.is_float(self._var_filter_spot_sizes_max.get()):
                self.initial_focus = self._ui_filter_spot_sizes_max
                self._ui_filter_spot_sizes_max_tip.showtip()
                return False
            spot_sizes_min = float(self._var_filter_spot_sizes_min.get())
            spot_sizes_max = float(self._var_filter_spot_sizes_max.get())
            if spot_sizes_min > spot_sizes_max:
                self.initial_focus = self._ui_filter_spot_sizes_max
                self._ui_filter_spot_sizes_max_tip.showtip()
                return False
        if self._var_filter_photons.get():
            if not self.is_float(self._var_filter_photons_min.get()):
                self.initial_focus = self._ui_filter_photons_min
                self._ui_filter_photons_min_tip.showtip()
                return False
            if not self.is_float(self._var_filter_photons_max.get()):
                self.initial_focus = self._ui_filter_photons_max
                self._ui_filter_photons_max_tip.showtip()
                return False
            photons_min = float(self._var_filter_photons_min.get())
            photons_max = float(self._var_filter_photons_max.get())
            if photons_min > photons_max:
                self.initial_focus = self._ui_filter_photons_max
                self._ui_filter_photons_max_tip.showtip()
                return False

        return super().validate()

    def process(self) -> None:
        self.model.cfg.filter_lenses = self._var_filter_lenses.get()

        if self._var_filter_rhos.get():
            self.model.cfg.filter_rhos = [
                float(self._var_filter_rhos_min.get()),
                float(self._var_filter_rhos_max.get())]
        else:
            self.model.cfg.filter_rhos = None

        if self._var_filter_spot_sizes.get():
            self.model.cfg.filter_spot_sizes = [
                float(self._var_filter_spot_sizes_min.get()),
                float(self._var_filter_spot_sizes_max.get())]
        else:
            self.model.cfg.filter_spot_sizes = None

        if self._var_filter_photons.get():
            self.model.cfg.filter_photons = [
                float(self._var_filter_photons_min.get()),
                float(self._var_filter_photons_max.get())]
        else:
            self.model.cfg.filter_photons = None

        self.model.cfg.alpha_model = smlfm.Localisations.AlphaModel[
            self._var_alpha_model.get()]

        super().process()

    def enable(self, active: bool, change_cursor: bool = True) -> None:
        super().enable(active, change_cursor)

        if active:
            state = tk.NORMAL if self._var_filter_rhos.get() else tk.DISABLED
            self._ui_filter_rhos_min.configure(state=state)
            self._ui_filter_rhos_max.configure(state=state)

            state = tk.NORMAL if self._var_filter_spot_sizes.get() else tk.DISABLED
            self._ui_filter_spot_sizes_min.configure(state=state)
            self._ui_filter_spot_sizes_max.configure(state=state)

            state = tk.NORMAL if self._var_filter_photons.get() else tk.DISABLED
            self._ui_filter_photons_min.configure(state=state)
            self._ui_filter_photons_max.configure(state=state)

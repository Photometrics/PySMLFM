import tkinter as tk
from idlelib.tooltip import Hovertip
from tkinter import ttk
from typing import Callable, Optional

import numpy as np

from .app_model import AppModel
from .cfg_dialog import CfgDialog


class CorrectCfgDialog(CfgDialog):

    def __init__(self, parent, model: AppModel, title: Optional[str] = None,
                 process_cb: Optional[Callable[[bool], None]] = None):
        if title is None:
            title = 'Correction Settings'

        self._ui_frames_min: Optional[ttk.Entry] = None
        self._var_frames_min = tk.StringVar(
            value=str(model.cfg.fit_params_aberration.frame_min))
        self._ui_frames_min_tip: Optional[Hovertip] = None
        self._ui_frames_max: Optional[ttk.Entry] = None
        self._var_frames_max = tk.StringVar(
            value=str(model.cfg.fit_params_aberration.frame_max))
        self._ui_frames_max_tip: Optional[Hovertip] = None

        self._ui_disparity_max: Optional[ttk.Entry] = None
        self._var_disparity_max = tk.StringVar(
            value=str(model.cfg.fit_params_aberration.disparity_max))
        self._ui_disparity_max_tip: Optional[Hovertip] = None

        self._ui_disparity_step: Optional[ttk.Entry] = None
        self._var_disparity_step = tk.StringVar(
            value=str(model.cfg.fit_params_aberration.disparity_step))
        self._ui_disparity_step_tip: Optional[Hovertip] = None

        self._ui_dist_search: Optional[ttk.Entry] = None
        self._var_dist_search = tk.StringVar(
            value=str(model.cfg.fit_params_aberration.dist_search))
        self._ui_dist_search_tip: Optional[Hovertip] = None

        self._ui_angle_tolerance: Optional[ttk.Entry] = None
        self._var_angle_tolerance = tk.StringVar(
            value=str(model.cfg.fit_params_aberration.angle_tolerance))
        self._ui_angle_tolerance_tip: Optional[Hovertip] = None

        self._ui_threshold: Optional[ttk.Entry] = None
        self._var_threshold = tk.StringVar(
            value=str(model.cfg.fit_params_aberration.threshold))
        self._ui_threshold_tip: Optional[Hovertip] = None

        self._ui_min_views: Optional[ttk.Entry] = None
        self._var_min_views = tk.StringVar(
            value=str(model.cfg.fit_params_aberration.min_views))
        self._ui_min_views_tip: Optional[Hovertip] = None

        self._ui_axial_window: Optional[ttk.Entry] = None
        self._var_axial_window = tk.StringVar(
            value=str(model.cfg.aberration_params.axial_window))
        self._ui_axial_window_tip: Optional[Hovertip] = None

        self._ui_photon_threshold: Optional[ttk.Entry] = None
        self._var_photon_threshold = tk.StringVar(
            value=str(model.cfg.aberration_params.photon_threshold))
        self._ui_photon_threshold_tip: Optional[Hovertip] = None

        super().__init__(parent, model, title, process_cb=process_cb)

    # noinspection PyProtectedMember, PyBroadException
    def body(self, master):
        ui_tab = ttk.Frame(master)
        row = 0

        try:
            nrs = self.model.lfl.locs_2d[:, 0]
            limits = (f'\n\nFor current data'
                      f' MIN={int(np.min(nrs))}, MAX={int(np.max(nrs))}')
        except BaseException:
            limits = ''
        #
        ui_frames_lbl = ttk.Label(ui_tab, text='Frame numbers:', anchor=tk.E)
        Hovertip(ui_frames_lbl,
                 text=(self.model.cfg._fit_params_aberration_doc
                       + '\nA range of frame numbers included in correction.'
                       + limits))
        self._ui_frames_min = ttk.Entry(
            ui_tab, textvariable=self._var_frames_min)
        self._ui_frames_min_tip = Hovertip(
            self._ui_frames_min,
            text=(self.model.cfg._fit_params_aberration_doc + '\n'
                  + self.model.cfg._fit_params_aberration_frame_min_doc
                  + limits))
        self.ui_widgets.append(self._ui_frames_min)
        self._ui_frames_max = ttk.Entry(
            ui_tab, textvariable=self._var_frames_max)
        self._ui_frames_max_tip = Hovertip(
            self._ui_frames_max,
            text=(self.model.cfg._fit_params_aberration_doc + '\n'
                  + self.model.cfg._fit_params_aberration_frame_max_doc
                  + limits))
        self.ui_widgets.append(self._ui_frames_max)
        #
        ui_frames_lbl.grid(column=0, row=row, sticky=tk.EW)
        self._ui_frames_min.grid(column=1, row=row, sticky=tk.EW)
        self._ui_frames_max.grid(column=2, row=row, sticky=tk.EW)
        row += 1

        ui_disparity_max_lbl = ttk.Label(ui_tab, text='Max. disparity:', anchor=tk.E)
        Hovertip(ui_disparity_max_lbl,
                 text=(self.model.cfg._fit_params_aberration_doc + '\n'
                       + self.model.cfg._fit_params_aberration_disparity_max_doc))
        self._ui_disparity_max = ttk.Entry(
            ui_tab, textvariable=self._var_disparity_max)
        self._ui_disparity_max_tip = Hovertip(
            self._ui_disparity_max,
            text=(self.model.cfg._fit_params_aberration_doc + '\n'
                  + self.model.cfg._fit_params_aberration_disparity_max_doc))
        self.ui_widgets.append(self._ui_disparity_max)
        ui_disparity_max_unit = ttk.Label(ui_tab, text=u'\u00B5m')  # microns
        #
        ui_disparity_max_lbl.grid(column=0, row=row, sticky=tk.EW)
        self._ui_disparity_max.grid(column=1, row=row, sticky=tk.EW, columnspan=2)
        ui_disparity_max_unit.grid(column=3, row=row, sticky=tk.W)
        row += 1

        ui_disparity_step_lbl = ttk.Label(ui_tab, text='Disparity step:', anchor=tk.E)
        Hovertip(ui_disparity_step_lbl,
                 text=(self.model.cfg._fit_params_aberration_doc + '\n'
                       + self.model.cfg._fit_params_aberration_disparity_step_doc))
        self._ui_disparity_step = ttk.Entry(
            ui_tab, textvariable=self._var_disparity_step)
        self._ui_disparity_step_tip = Hovertip(
            self._ui_disparity_step,
            text=(self.model.cfg._fit_params_aberration_doc + '\n'
                  + self.model.cfg._fit_params_aberration_disparity_step_doc))
        self.ui_widgets.append(self._ui_disparity_step)
        ui_disparity_step_unit = ttk.Label(ui_tab, text=u'\u00B5m')  # microns
        #
        ui_disparity_step_lbl.grid(column=0, row=row, sticky=tk.EW)
        self._ui_disparity_step.grid(column=1, row=row, sticky=tk.EW, columnspan=2)
        ui_disparity_step_unit.grid(column=3, row=row, sticky=tk.W)
        row += 1

        ui_dist_search_lbl = ttk.Label(ui_tab, text='Search distance:', anchor=tk.E)
        Hovertip(ui_dist_search_lbl,
                 text=(self.model.cfg._fit_params_aberration_doc + '\n'
                       + self.model.cfg._fit_params_aberration_dist_search_doc))
        self._ui_dist_search = ttk.Entry(
            ui_tab, textvariable=self._var_dist_search)
        self._ui_dist_search_tip = Hovertip(
            self._ui_dist_search,
            text=(self.model.cfg._fit_params_aberration_doc + '\n'
                  + self.model.cfg._fit_params_aberration_dist_search_doc))
        self.ui_widgets.append(self._ui_dist_search)
        ui_dist_search_unit = ttk.Label(ui_tab, text=u'\u00B5m')  # microns
        #
        ui_dist_search_lbl.grid(column=0, row=row, sticky=tk.EW)
        self._ui_dist_search.grid(column=1, row=row, sticky=tk.EW, columnspan=2)
        ui_dist_search_unit.grid(column=3, row=row, sticky=tk.W)
        row += 1

        ui_angle_tolerance_lbl = ttk.Label(ui_tab, text='Angle tolerance:', anchor=tk.E)
        Hovertip(ui_angle_tolerance_lbl,
                 text=(self.model.cfg._fit_params_aberration_doc + '\n'
                       + self.model.cfg._fit_params_aberration_angle_tolerance_doc))
        self._ui_angle_tolerance = ttk.Entry(
            ui_tab, textvariable=self._var_angle_tolerance)
        self._ui_angle_tolerance_tip = Hovertip(
            self._ui_angle_tolerance,
            text=(self.model.cfg._fit_params_aberration_doc + '\n'
                  + self.model.cfg._fit_params_aberration_angle_tolerance_doc))
        self.ui_widgets.append(self._ui_angle_tolerance)
        ui_angle_tolerance_unit = ttk.Label(ui_tab, text='deg')
        #
        ui_angle_tolerance_lbl.grid(column=0, row=row, sticky=tk.EW)
        self._ui_angle_tolerance.grid(column=1, row=row, sticky=tk.EW, columnspan=2)
        ui_angle_tolerance_unit.grid(column=3, row=row, sticky=tk.W)
        row += 1

        ui_threshold_lbl = ttk.Label(ui_tab, text='Threshold:', anchor=tk.E)
        Hovertip(ui_threshold_lbl,
                 text=(self.model.cfg._fit_params_aberration_doc + '\n'
                       + self.model.cfg._fit_params_aberration_threshold_doc))
        self._ui_threshold = ttk.Entry(
            ui_tab, textvariable=self._var_threshold)
        self._ui_threshold_tip = Hovertip(
            self._ui_threshold,
            text=(self.model.cfg._fit_params_aberration_doc + '\n'
                  + self.model.cfg._fit_params_aberration_threshold_doc))
        self.ui_widgets.append(self._ui_threshold)
        ui_threshold_unit = ttk.Label(ui_tab, text=u'\u00B5m')  # microns
        #
        ui_threshold_lbl.grid(column=0, row=row, sticky=tk.EW)
        self._ui_threshold.grid(column=1, row=row, sticky=tk.EW, columnspan=2)
        ui_threshold_unit.grid(column=3, row=row, sticky=tk.W)
        row += 1

        ui_min_views_lbl = ttk.Label(ui_tab, text='Min. views:', anchor=tk.E)
        Hovertip(ui_min_views_lbl,
                 text=(self.model.cfg._fit_params_aberration_doc + '\n'
                       + self.model.cfg._fit_params_aberration_min_views_doc))
        self._ui_min_views = ttk.Entry(
            ui_tab, textvariable=self._var_min_views)
        self._ui_min_views_tip = Hovertip(
            self._ui_min_views,
            text=(self.model.cfg._fit_params_aberration_doc + '\n'
                  + self.model.cfg._fit_params_aberration_min_views_doc))
        self.ui_widgets.append(self._ui_min_views)
        #
        ui_min_views_lbl.grid(column=0, row=row, sticky=tk.EW)
        self._ui_min_views.grid(column=1, row=row, sticky=tk.EW, columnspan=2)
        row += 1

        ui_axial_window_lbl = ttk.Label(ui_tab, text='Axial window:', anchor=tk.E)
        Hovertip(ui_axial_window_lbl,
                 text=(self.model.cfg._aberration_params_doc + '\n'
                       + self.model.cfg._aberration_params_axial_window_doc))
        self._ui_axial_window = ttk.Entry(
            ui_tab, textvariable=self._var_axial_window)
        self._ui_axial_window_tip = Hovertip(
            self._ui_axial_window,
            text=(self.model.cfg._aberration_params_doc + '\n'
                  + self.model.cfg._aberration_params_axial_window_doc))
        self.ui_widgets.append(self._ui_axial_window)
        ui_axial_window_unit = ttk.Label(ui_tab, text=u'\u00B5m')  # microns
        #
        ui_axial_window_lbl.grid(column=0, row=row, sticky=tk.EW)
        self._ui_axial_window.grid(column=1, row=row, sticky=tk.EW, columnspan=2)
        ui_axial_window_unit.grid(column=3, row=row, sticky=tk.W)
        row += 1

        ui_photon_threshold_lbl = ttk.Label(ui_tab, text='Photon threshold:', anchor=tk.E)
        Hovertip(ui_photon_threshold_lbl,
                 text=(self.model.cfg._aberration_params_doc + '\n'
                       + self.model.cfg._aberration_params_photon_threshold_doc))
        self._ui_photon_threshold = ttk.Entry(
            ui_tab, textvariable=self._var_photon_threshold)
        self._ui_photon_threshold_tip = Hovertip(
            self._ui_photon_threshold,
            text=(self.model.cfg._aberration_params_doc + '\n'
                  + self.model.cfg._aberration_params_photon_threshold_doc))
        self.ui_widgets.append(self._ui_photon_threshold)
        #
        ui_photon_threshold_lbl.grid(column=0, row=row, sticky=tk.EW)
        self._ui_photon_threshold.grid(column=1, row=row, sticky=tk.EW, columnspan=2)
        row += 1

        # Final padding and layout
        ui_tab.columnconfigure(index=1, weight=1)
        ui_tab.columnconfigure(index=2, weight=1)
        self.model.grid_slaves_configure(ui_tab, padx=1, pady=1)

        ui_tab.pack(anchor=tk.NW, fill=tk.X, expand=True, padx=5, pady=5)

        return self._ui_frames_max  # Control that gets initial focus

    def validate(self):
        if not self.is_int(self._var_frames_min.get()):
            self.initial_focus = self._ui_frames_min
            self._ui_frames_min_tip.showtip()
            return False
        if not self.is_int(self._var_frames_max.get()):
            self.initial_focus = self._ui_frames_max
            self._ui_frames_max_tip.showtip()
            return False
        frames_min = int(self._var_frames_min.get())
        frames_max = int(self._var_frames_max.get())
        if frames_min > frames_max:
            self.initial_focus = self._ui_frames_max
            self._ui_frames_max_tip.showtip()
            return False
        if not self.is_float(self._var_disparity_max.get()):
            self.initial_focus = self._ui_disparity_max
            self._ui_disparity_max_tip.showtip()
            return False
        if not self.is_float(self._var_disparity_step.get()):
            self.initial_focus = self._ui_disparity_step
            self._ui_disparity_step_tip.showtip()
            return False
        if not self.is_float(self._var_dist_search.get()):
            self.initial_focus = self._ui_dist_search
            self._ui_dist_search_tip.showtip()
            return False
        if not self.is_float(self._var_angle_tolerance.get()):
            self.initial_focus = self._ui_angle_tolerance
            self._ui_angle_tolerance_tip.showtip()
            return False
        if not self.is_float(self._var_threshold.get()):
            self.initial_focus = self._ui_threshold
            self._ui_threshold_tip.showtip()
            return False
        if not self.is_int(self._var_min_views.get()):
            self.initial_focus = self._ui_min_views
            self._ui_min_views_tip.showtip()
            return False

        if not self.is_float(self._var_axial_window.get()):
            self.initial_focus = self._ui_axial_window
            self._ui_axial_window_tip.showtip()
            return False
        if not self.is_int(self._var_photon_threshold.get()):
            self.initial_focus = self._ui_photon_threshold
            self._ui_photon_threshold_tip.showtip()
            return False

        return super().validate()

    def process(self):
        self.model.cfg.fit_params_aberration.frame_min = (
            int(self._var_frames_min.get()))
        self.model.cfg.fit_params_aberration.frame_max = (
            int(self._var_frames_max.get()))
        self.model.cfg.fit_params_aberration.disparity_max = (
            float(self._var_disparity_max.get()))
        self.model.cfg.fit_params_aberration.disparity_step = (
            float(self._var_disparity_step.get()))
        self.model.cfg.fit_params_aberration.dist_search = (
            float(self._var_dist_search.get()))
        self.model.cfg.fit_params_aberration.angle_tolerance = (
            float(self._var_angle_tolerance.get()))
        self.model.cfg.fit_params_aberration.threshold = (
            float(self._var_threshold.get()))
        self.model.cfg.fit_params_aberration.min_views = (
            int(self._var_min_views.get()))

        self.model.cfg.aberration_params.axial_window = (
            float(self._var_axial_window.get()))
        self.model.cfg.aberration_params.photon_threshold = (
            int(self._var_photon_threshold.get()))

        # Used the same value from cfg.fit_params_aberration
        self.model.cfg.aberration_params.min_views = int(self._var_min_views.get())

        super().process()
import dataclasses
import multiprocessing as mp
import time
import tkinter as tk
import traceback as tb
from datetime import datetime
from idlelib.tooltip import Hovertip
from pathlib import Path
from threading import Thread
from tkinter import filedialog, messagebox, ttk
from typing import Optional

import numpy as np
import numpy.typing as npt
from matplotlib.figure import Figure

import smlfm
import smlfm.graphs

from .app_model import AppModel, IStage
from .consts import COMMAND, IMAGE, TEXT, TEXTVARIABLE, VARIABLE, GraphType, StageType
from .figure_window import FigureWindow
from .fit_cfg_dialog import FitCfgDialog


# pylint: disable=too-many-ancestors,too-many-instance-attributes
class FitFrame(ttk.Frame, IStage):

    # pylint: disable=too-many-statements
    def __init__(self, master, model: AppModel, *args, **kwargs):
        super().__init__(master, *args, **kwargs)

        self._stage_type = StageType.FIT
        self._stage_type_next = None

        self._model = model

        # Controls
        self._ui_frm_lbl = ttk.Label(self)
        self._ui_frm = ttk.LabelFrame(self, labelwidget=self._ui_frm_lbl)

        self._ui_tab = ttk.Frame(self._ui_frm)
        self._ui_autosave_dir_chb = ttk.Checkbutton(self._ui_tab)
        self._ui_autosave_dir_chb_tip = Hovertip(self._ui_autosave_dir_chb, text='')
        self._ui_save_dir = ttk.Entry(self._ui_tab)
        self._ui_save_dir_tip = Hovertip(self._ui_save_dir, text='')
        self._ui_save_dir_btn = ttk.Button(self._ui_tab)
        self._ui_save_as = ttk.Button(self._ui_tab)

        self._ui_summary = ttk.Frame(self._ui_frm)
        self._ui_settings = ttk.Checkbutton(self._ui_summary, style='Toolbutton')
        self._ui_settings_tip = Hovertip(self._ui_settings, text='')
        self._ui_start = ttk.Checkbutton(self._ui_summary, style='Toolbutton')
        self._ui_start_tip = Hovertip(self._ui_start, text='')
        self._ui_summary_lbl = ttk.Label(self._ui_summary)
        self._ui_preview_occ = ttk.Checkbutton(self._ui_summary, style='Toolbutton')
        self._ui_preview_occ_tip = Hovertip(self._ui_preview_occ, text='')
        self._ui_preview_hist = ttk.Checkbutton(self._ui_summary, style='Toolbutton')
        self._ui_preview_hist_tip = Hovertip(self._ui_preview_hist, text='')
        self._ui_preview_3d = ttk.Checkbutton(self._ui_summary, style='Toolbutton')
        self._ui_preview_3d_tip = Hovertip(self._ui_preview_3d, text='')

        self._ui_progress = ttk.Progressbar(
            self._ui_frm, orient=tk.HORIZONTAL, mode='determinate')

        # Layout
        self._ui_autosave_dir_chb.grid(column=0, row=0, sticky=tk.E)
        self._ui_save_dir.grid(column=1, row=0, sticky=tk.EW)
        self._ui_save_dir_btn.grid(column=2, row=0, sticky=tk.W)
        self._ui_save_as.grid(column=1, row=1, sticky=tk.W)
        self._ui_tab.columnconfigure(index=1, weight=1)

        self._ui_settings.grid(column=0, row=0, sticky=tk.NW)
        self._ui_start.grid(column=1, row=0, sticky=tk.NW)
        self._ui_summary_lbl.grid(column=2, row=0, sticky=tk.EW)
        self._ui_preview_occ.grid(column=3, row=0, sticky=tk.NW)
        self._ui_preview_hist.grid(column=4, row=0, sticky=tk.NW)
        self._ui_preview_3d.grid(column=5, row=0, sticky=tk.NW)
        self._ui_summary.columnconfigure(index=2, weight=1)

        self._ui_tab.grid(column=0, row=0, sticky=tk.EW)
        self._ui_summary.grid(column=0, row=1, sticky=tk.EW)
        self._ui_progress.grid(column=0, row=2, sticky=tk.EW)
        self._ui_frm.columnconfigure(index=0, weight=1)

        self._ui_frm.grid(column=0, row=0, sticky=tk.EW)
        self.columnconfigure(index=0, weight=1)

        # Padding
        self._model.grid_slaves_configure(self._ui_tab, padx=1, pady=1)
        self._ui_tab.configure(padding=0)
        self._model.grid_slaves_configure(self._ui_summary, padx=1, pady=1)
        self._model.grid_slaves_configure(self._ui_frm, padx=5, pady=(0, 5))
        self._ui_frm.configure(padding=0)

        # Texts & icons
        self._ui_frm_lbl.configure(text='Fitting',
                                   image=self._model.icons.fit_stage,
                                   compound=tk.LEFT)
        self._ui_autosave_dir_chb[TEXT] = 'Autosave to:'
        self._ui_autosave_dir_chb_tip.text = (
            'Results are saved under this directory to a new sub-folder\n'
            'with a name containing a timestamp of execution.')
        self._ui_save_dir_tip.text = self._ui_autosave_dir_chb_tip.text
        self._ui_save_dir_btn.configure(text='...', width=3)
        self._ui_save_as.configure(text='Save as',
                                   image=self._model.icons.save_as,
                                   compound=tk.LEFT)
        self._ui_settings[IMAGE] = self._model.icons.settings
        self._ui_settings_tip.text = 'Edit parameters'
        self._ui_start[IMAGE] = self._model.icons.start
        self._ui_start_tip.text = 'Proceed with fitting'
        self._ui_preview_occ[IMAGE] = self._model.icons.fit_occurrences
        self._ui_preview_occ_tip.text = 'Preview occurrences'
        self._ui_preview_hist[IMAGE] = self._model.icons.fit_histogram
        self._ui_preview_hist_tip.text = 'Preview histogram'
        self._ui_preview_3d[IMAGE] = self._model.icons.fit_3d
        self._ui_preview_3d_tip.text = 'Final 3D localisations'
        self._ui_progress.configure()

        # Hooks
        self._ui_autosave_dir_chb[COMMAND] = self._on_autosave_dir
        self._ui_save_dir.bind(
            '<FocusOut>', lambda _e: self._on_save_dir_leave())
        self._ui_save_dir_btn[COMMAND] = self._on_get_save_dir
        self._ui_save_as[COMMAND] = self._on_save_as
        self._ui_settings[COMMAND] = self._on_settings
        self._ui_start[COMMAND] = self._on_start
        self._ui_summary.bind(
            '<Configure>', lambda _e: self._ui_summary_lbl.configure(
                wraplength=self._ui_summary_lbl.winfo_width()))
        self._ui_preview_occ[COMMAND] = self._on_preview_occ
        self._ui_preview_hist[COMMAND] = self._on_preview_hist
        self._ui_preview_3d[COMMAND] = self._on_preview_3d

        # Data
        self._var_autosave_dir_chb = tk.IntVar()
        self._ui_autosave_dir_chb[VARIABLE] = self._var_autosave_dir_chb
        self._var_save_dir = tk.StringVar()
        self._ui_save_dir[TEXTVARIABLE] = self._var_save_dir
        self._var_settings = tk.IntVar()
        self._ui_settings[VARIABLE] = self._var_settings
        self._var_start = tk.IntVar()
        self._ui_start[VARIABLE] = self._var_start
        self._var_summary = tk.StringVar()
        self._ui_summary_lbl[TEXTVARIABLE] = self._var_summary
        self._var_preview_occ = tk.IntVar()
        self._ui_preview_occ[VARIABLE] = self._var_preview_occ
        self._var_preview_hist = tk.IntVar()
        self._ui_preview_hist[VARIABLE] = self._var_preview_hist
        self._var_preview_3d = tk.IntVar()
        self._ui_preview_3d[VARIABLE] = self._var_preview_3d
        self._var_progress = tk.IntVar()
        self._ui_progress[VARIABLE] = self._var_progress

        self._update_thread: Optional[Thread] = None
        self._update_thread_err: Optional[str] = None
        self._update_thread_abort: Optional[mp.Event] = None

        self._settings_dlg: Optional[FitCfgDialog] = None
        self._settings_apply: bool = False
        self._update_from_settings: bool = False

        # =0 ~ disabled, >0 ~ remaining flashes, None ~ infinite
        self._flash_counter = 0
        self._flash_id = None

        # A cache with locs_3d filtered by max_lateral_err and min_view_count
        self._keep_idx: Optional[npt.NDArray[float]] = None

        self._saved_path: Optional[Path] = None

        self.stage_ui_init()

    def stage_type(self):
        return self._stage_type

    def stage_type_next(self):
        return self._stage_type_next

    def stage_is_active(self) -> bool:
        lfl = self._model.lfl
        return lfl is not None and lfl.correction is not None

    def stage_invalidate(self):
        self._flash_stop()

        self._model.locs_3d = None
        self._keep_idx = None
        self._saved_path = None

        if not self._update_from_settings:
            for gt in [GraphType.LOCS_3D, GraphType.HISTOGRAM, GraphType.OCCURRENCES]:
                self._model.destroy_graph(gt)

        self._model.stage_enabled(self._stage_type, False)

        self.stage_ui_init()
        self._model.stage_invalidate(self._stage_type_next)

    def stage_start_update(self):
        self.stage_invalidate()
        self._model.stages_ui_updating(True)
        self.winfo_toplevel().configure(cursor='watch')

        self._model.save_timestamp = datetime.now()

        self._ui_start[IMAGE] = self._model.icons.cancel
        self._ui_start_tip.text = 'Abort processing'
        self._ui_start.configure(state=tk.NORMAL)

        frame_min = (self._model.cfg.fit_params_full.frame_min
                     if self._model.cfg.fit_params_full.frame_min > 0
                     else self._model.lfl.min_frame)
        frame_max = (self._model.cfg.fit_params_full.frame_max
                     if self._model.cfg.fit_params_full.frame_max > 0
                     else self._model.lfl.max_frame)
        self._ui_progress.configure(maximum=frame_max - frame_min + 1)
        self._var_progress.set(0)

        def _update_thread_fn():
            try:
                self._update_task()
            except BaseException as ex:
                self._update_thread_err = str(ex)
                tb.print_exception(None, ex, ex.__traceback__)

            def _update_done():
                self._ui_start[IMAGE] = self._model.icons.start
                self._ui_start_tip.text = 'Proceed with fitting'
                self._ui_start.configure(state=tk.DISABLED)

                self._update_thread = None
                self.winfo_toplevel().configure(cursor='')

                self._model.stages_ui_updating(False)

                # Reset the flag after the stage update prints it was aborted
                self._update_thread_abort = None

                if self._update_thread_err is not None:
                    err = self._update_thread_err
                    self._update_thread_err = None

                    if self._model.locs_3d is None:
                        messagebox.showerror(
                            title='Fitting Error',
                            message=f'The fitting failed:\n{err}')
                    else:
                        messagebox.showerror(
                            title='File Error',
                            message=f'The results cannot be saved:\n{err}')

                    self._settings_apply = False
                    self._update_from_settings = False

                    self.stage_invalidate()
                    return

                # if self._model.stage_is_active(self._stage_type_next):
                if self._model.locs_3d is not None:

                    self._show_previews(force_update=True)

                    self._model.stage_ui_init(self._stage_type_next)
                    # Next phase updates automatically or the user continues manually
                    if self._update_from_settings:
                        self._model.stage_ui_flash(self._stage_type_next)
                    else:
                        if self._model.cfg.confirm_mla_alignment:
                            self._model.stage_ui_flash(self._stage_type_next)
                        else:
                            self._model.stage_start_update(self._stage_type_next)

                self._settings_apply = False
                self._update_from_settings = False

            self._model.invoke_on_gui_thread_async(_update_done)

        self._update_thread_abort = mp.Event()
        self._update_thread = Thread(target=_update_thread_fn, daemon=True)
        self._update_thread.start()

    def stage_ui_init(self):
        if self._model.cfg is not None:
            if self._model.cfg.save_dir is None:
                self._var_autosave_dir_chb.set(0)
                self._var_save_dir.set('')
            else:
                self._var_autosave_dir_chb.set(1)
                self._var_save_dir.set(str(self._model.cfg.save_dir))

        self._ui_update_done()

    def stage_ui_flash(self):
        self._flash_start()

    def stage_ui_updating(self, updating: bool):
        if updating:
            self._ui_update_start()
        else:
            self._ui_update_done()

    def _ui_update_start(self):
        self._ui_autosave_dir_chb.configure(state=tk.DISABLED)
        self._ui_save_dir.configure(state=tk.DISABLED)
        self._ui_save_dir_btn.configure(state=tk.DISABLED)
        self._ui_save_as.configure(state=tk.DISABLED)
        self._ui_settings.configure(state=tk.DISABLED)
        if self._update_from_settings:
            settings_dlg = self._settings_dlg
            if settings_dlg is not None:
                settings_dlg.enable(False)
        self._ui_start.configure(state=tk.DISABLED)
        self._ui_preview_occ.configure(state=tk.DISABLED)
        self._ui_preview_hist.configure(state=tk.DISABLED)
        self._ui_preview_3d.configure(state=tk.DISABLED)

    # pylint: disable=too-many-branches
    def _ui_update_done(self):
        self._ui_update_start()

        if self.stage_is_active():
            self._model.stage_enabled(self._stage_type, True)

            self._ui_autosave_dir_chb.configure(state=tk.NORMAL)
            if self._var_autosave_dir_chb.get():
                self._ui_save_dir.configure(state=tk.NORMAL)
                self._ui_save_dir_btn.configure(state=tk.NORMAL)
            else:
                self._ui_save_dir.configure(state=tk.DISABLED)
                self._ui_save_dir_btn.configure(state=tk.DISABLED)
            self._ui_settings.configure(state=tk.NORMAL)
            if self._update_from_settings:
                settings_dlg = self._settings_dlg
                if settings_dlg is not None:
                    settings_dlg.enable(True)
            self._ui_start.configure(state=tk.NORMAL)

            # if self._model.stage_is_active(self._stage_type_next):
            if self._model.locs_3d is not None:
                if self._var_autosave_dir_chb.get():
                    self._ui_save_as.configure(state=tk.DISABLED)
                else:
                    self._ui_save_as.configure(state=tk.NORMAL)
                self._ui_preview_occ.configure(state=tk.NORMAL)
                self._ui_preview_hist.configure(state=tk.NORMAL)
                self._ui_preview_3d.configure(state=tk.NORMAL)

                points = self._model.locs_3d.shape[0]
                frames = np.unique(self._model.locs_3d[:, 7]).shape[0]
                views = int(np.sum(self._model.locs_3d[:, 5]))
                fit_msg = (
                    f'Fitting completed with {points} 3D localisations,'
                    f' used {frames} frames and {views} 2D localisations in total')
                if self._saved_path is not None:
                    self._var_summary.set(
                        f'{fit_msg}.\n'
                        f'Results saved to folder: "{self._saved_path.name}"')
                else:
                    self._var_summary.set(fit_msg)
            else:
                if (self._update_thread_abort is not None
                        and self._update_thread_abort.is_set()):
                    self._var_summary.set('Fitting aborted')
                else:
                    self._var_summary.set('No fitting done')
        else:
            self._var_summary.set('No fitting done yet')

        # Set progress bar full
        self._ui_progress.stop()
        self._ui_progress.configure(maximum=100)
        self._var_progress.set(100)

    def _flash_start(self):
        self._flash_stop()

        def _toggle_on():
            if self._flash_counter is None or self._flash_counter > 0:
                self._var_start.set(1)
                self._flash_id = self.after(500, _toggle_off)

        def _toggle_off():
            self._var_start.set(0)
            if self._flash_counter is None or self._flash_counter > 0:
                if self._flash_counter is not None:
                    self._flash_counter -= 1
                self._flash_id = self.after(500, _toggle_on)

        self._flash_counter = None
        _toggle_on()

    def _flash_stop(self):
        self._flash_counter = 0
        if self._flash_id is not None:
            self.after_cancel(self._flash_id)
        self._var_start.set(0)

    def _on_autosave_dir(self):
        if self._var_autosave_dir_chb.get():
            dir_name = self._var_save_dir.get()
            if dir_name:
                self._model.cfg.save_dir = Path(dir_name)
            else:
                self._model.cfg.save_dir = None

            self._ui_save_dir.configure(state=tk.NORMAL)
            self._ui_save_dir_btn.configure(state=tk.NORMAL)
            if self._model.locs_3d is not None:
                self._ui_save_as.configure(state=tk.DISABLED)
        else:
            self._model.cfg.save_dir = None

            self._ui_save_dir.configure(state=tk.DISABLED)
            self._ui_save_dir_btn.configure(state=tk.DISABLED)
            if self._model.locs_3d is not None:
                self._ui_save_as.configure(state=tk.NORMAL)

    def _on_save_dir_leave(self):
        dir_name = self._var_save_dir.get()
        self._model.cfg.save_dir = Path(dir_name) if dir_name else None

    def _on_get_save_dir(self):
        initial_dir = None
        if self._model.cfg.save_dir is not None:
            initial_dir = self._model.cfg.save_dir

        dir_name = filedialog.askdirectory(
            parent=self,
            title='Select top-level folder for results...',
            initialdir=initial_dir)
        if dir_name:
            self._var_save_dir.set(dir_name)
            self._model.cfg.save_dir = Path(dir_name)

    def _on_save_as(self):
        initial_dir = None
        if self._model.cfg.save_dir is not None:
            initial_dir = self._model.cfg.save_dir

        dir_name = filedialog.askdirectory(
            parent=self,
            title='Select folder for results...',
            initialdir=initial_dir)
        if dir_name:
            bak = self._model.cfg.save_dir
            try:
                # Resolve to absolute path to not get a sub-folder with timestamp
                # Change save path temporarily to have it stored with results,
                # but enabled autosave afterward.
                self._model.cfg.save_dir = Path(dir_name).resolve()
                self._saved_path = self.save(self._model.cfg.save_dir)
            finally:
                self._model.cfg.save_dir = bak
                self._ui_update_done()

    def _on_settings(self):
        cfg_dump_old = self._model.cfg.to_json()

        def _process_cb(apply: bool):
            self._settings_apply = apply
            self._update_from_settings = True
            nonlocal cfg_dump_old
            cfg_dump_new = self._model.cfg.to_json()
            if (cfg_dump_old != cfg_dump_new
                    # not self._model.stage_is_active(self._stage_type_next)
                    or self._model.locs_3d is None):
                cfg_dump_old = cfg_dump_new
                self.stage_start_update()
            else:
                self._show_previews()
                self._settings_apply = False
                self._update_from_settings = False

        self._settings_dlg = FitCfgDialog(self, self._model, process_cb=_process_cb)
        self._settings_dlg.show_modal()
        self._settings_dlg = None
        if (not self._var_preview_occ.get()
                and not self._var_preview_hist.get()
                and not self._var_preview_3d.get()):
            self._settings_apply = False
            self._update_from_settings = False
        self._var_settings.set(0)

    def _on_start(self):
        self._var_start.set(0)

        if self._update_thread is not None:
            if self._update_thread_abort is not None:
                if not self._update_thread_abort.is_set():
                    self._ui_start.configure(state=tk.DISABLED)
                    self._var_summary.set('Aborting...')
                    self._update_thread_abort.set()
        else:
            self._flash_stop()
            self.stage_start_update()

    def _show_previews(self, force_update: bool = False):
        # if not self._model.stage_is_active(self._stage_type_next):
        if self._model.locs_3d is None:
            return

        show = self._model.cfg.show_graphs and self._model.cfg.show_result_graphs

        force_show_occ = show and self._model.cfg.show_all_debug_graphs
        force_update_occ = (force_update
                            and self._model.graph_exists(GraphType.OCCURRENCES))
        if force_show_occ:
            self._var_preview_occ.set(1)
        if force_show_occ or force_update_occ:
            self._on_preview_occ(force_update_occ)

        force_show_hist = show and self._model.cfg.show_all_debug_graphs
        force_update_hist = (force_update
                             and self._model.graph_exists(GraphType.HISTOGRAM))
        if force_show_hist:
            self._var_preview_hist.set(1)
        if force_show_hist or force_update_hist:
            self._on_preview_hist(force_update_hist)

        force_show_3d = show or self._settings_apply
        force_update_3d = (force_update
                           and self._model.graph_exists(GraphType.LOCS_3D))
        if force_show_3d:
            self._var_preview_3d.set(1)
        if force_show_3d or force_update_3d:
            self._on_preview_3d(force_update_3d)

    def _on_preview_occ(self, force_update: bool = False):

        def draw(f: Figure, set_size: bool = True) -> Figure:
            lateral_err = self._model.locs_3d[:, 3]  # Fitting error in X and Y (in microns)
            axial_err = self._model.locs_3d[:, 4]  # Fitting error in Z (in microns)
            photons = self._model.locs_3d[:, 6]  # Number of photons in fit
            return smlfm.graphs.draw_occurrences(
                f,
                lateral_err[self._keep_idx],
                axial_err[self._keep_idx],
                photons[self._keep_idx],
                set_default_size=set_size)

        wnd = self._model.graphs[GraphType.OCCURRENCES]
        if wnd is None:
            fig = draw(Figure())
            wnd = FigureWindow(fig, master=self, title='Occurrences')
            wnd.bind('<Map>', func=lambda _evt: self._var_preview_occ.set(1))
            wnd.bind('<Unmap>', func=lambda _evt: self._var_preview_occ.set(0))
            self._model.graphs[GraphType.OCCURRENCES] = wnd
        else:
            if force_update:
                draw(wnd.figure, set_size=False)
                wnd.refresh()

        if self._var_preview_occ.get():
            wnd.deiconify()
        else:
            wnd.withdraw()

    def _on_preview_hist(self, force_update: bool = False):

        def draw(f: Figure, set_size: bool = True) -> Figure:
            axial_err = self._model.locs_3d[:, 4]  # Fitting error in Z (in microns)
            photons = self._model.locs_3d[:, 6]  # Number of photons in fit
            return smlfm.graphs.draw_histogram(
                f,
                photons[self._keep_idx],
                axial_err[self._keep_idx],
                set_default_size=set_size)

        wnd = self._model.graphs[GraphType.HISTOGRAM]
        if wnd is None:
            fig = draw(Figure())
            wnd = FigureWindow(fig, master=self, title='Histogram')
            wnd.bind('<Map>', func=lambda _evt: self._var_preview_hist.set(1))
            wnd.bind('<Unmap>', func=lambda _evt: self._var_preview_hist.set(0))
            self._model.graphs[GraphType.HISTOGRAM] = wnd
        else:
            if force_update:
                draw(wnd.figure, set_size=False)
                wnd.refresh()

        if self._var_preview_hist.get():
            wnd.deiconify()
        else:
            wnd.withdraw()

    def _on_preview_3d(self, force_update: bool = False):

        def draw(f: Figure, set_size: bool = True) -> Figure:
            xyz = self._model.locs_3d[:, 0:3]  # X, Y, Z
            return smlfm.graphs.draw_3d_locs(
                f,
                xyz[self._keep_idx],
                set_default_size=set_size)

        wnd = self._model.graphs[GraphType.LOCS_3D]
        if wnd is None:
            fig = draw(Figure())
            wnd = FigureWindow(fig, master=self, title='3D')
            wnd.bind('<Map>', func=lambda _evt: self._var_preview_3d.set(1))
            wnd.bind('<Unmap>', func=lambda _evt: self._var_preview_3d.set(0))
            self._model.graphs[GraphType.LOCS_3D] = wnd
        else:
            if force_update:
                draw(wnd.figure, set_size=False)
                wnd.refresh()

        if self._var_preview_3d.get():
            wnd.deiconify()
        else:
            wnd.withdraw()

    # Executed on thread
    def _update_task(self):
        tic = time.time()

        fit_params_all = dataclasses.replace(
            self._model.cfg.fit_params_full,
            frame_min=(self._model.cfg.fit_params_full.frame_min
                       if self._model.cfg.fit_params_full.frame_min > 0
                       else self._model.lfl.min_frame),
            frame_max=(self._model.cfg.fit_params_full.frame_max
                       if self._model.cfg.fit_params_full.frame_max > 0
                       else self._model.lfl.max_frame),
        )

        self._model.invoke_on_gui_thread_async(
            self._var_summary.set,
            f'Fitting frames'
            f' {fit_params_all.frame_min}-{fit_params_all.frame_max}...')

        self._model.locs_3d, _ = smlfm.Fitting.light_field_fit(
            self._model.lfl.corrected_locs_2d,
            self._model.lfm.rho_scaling, fit_params_all,
            abort_event=self._update_thread_abort,
            progress_func=lambda frame, min_frame, _max_frame:
                self._model.invoke_on_gui_thread_async(
                    self._var_progress.set, frame - min_frame + 1),
            progress_step=100,
            worker_count=self._model.cfg.max_workers)

        if self._update_thread_abort is not None:
            if self._update_thread_abort.is_set():
                self._model.locs_3d = None
                return

        lateral_err = self._model.locs_3d[:, 3]  # Fitting error in X and Y (in microns)
        view_count = self._model.locs_3d[:, 5]  # Number of views used to fit the localisation
        max_lateral_err = self._model.cfg.show_max_lateral_err
        min_view_count = self._model.cfg.show_min_view_count
        self._keep_idx = np.logical_and(
            (lateral_err < max_lateral_err) if max_lateral_err is not None else True,
            (view_count > min_view_count) if min_view_count is not None else True)

        if self._model.cfg.log_timing:
            print(f'Complete fitting took {1e3 * (time.time() - tic):.3f} ms')

        if self._update_thread_abort is not None:
            if self._update_thread_abort.is_set():
                self._model.locs_3d = None
                self._keep_idx = None
                return

        if self._model.cfg.save_dir is not None:
            timestamp_str = self._model.save_timestamp.strftime('%Y%m%d-%H%M%S')
            sub_dir = Path(f'3D Fitting - {timestamp_str}'
                           f' - {self._model.cfg.csv_file.name}')
            self._saved_path = self.save(sub_dir)

    # Executed on both, main thread and update thread
    def save(self, folder: Path) -> Path:
        results = smlfm.OutputFiles(self._model.cfg, folder)

        results.mkdir()
        results.save_config()
        results.save_csv(self._model.locs_3d)
        results.save_visp(self._model.locs_3d)
        results.save_figures()

        return results.folder

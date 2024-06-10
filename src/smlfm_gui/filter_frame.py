import multiprocessing as mp
import time
import tkinter as tk
import traceback as tb
from idlelib.tooltip import Hovertip
from threading import Thread
from tkinter import messagebox, ttk
from typing import Optional

import numpy as np
from matplotlib.figure import Figure

import smlfm
import smlfm.graphs

from .app_model import AppModel, IStage
from .consts import COMMAND, IMAGE, TEXTVARIABLE, VARIABLE, GraphType, StageType
from .figure_window import FigureWindow
from .filter_cfg_dialog import FilterCfgDialog


# pylint: disable=too-many-ancestors
class FilterFrame(ttk.Frame, IStage):

    def __init__(self, master, model: AppModel, *args, **kwargs):
        super().__init__(master, *args, **kwargs)

        self._stage_type = StageType.FILTER
        self._stage_type_next = StageType.CORRECT

        self._model = model

        # Controls
        self._ui_frm_lbl = ttk.Label(self)
        self._ui_frm = ttk.LabelFrame(self, labelwidget=self._ui_frm_lbl)

        self._ui_summary = ttk.Frame(self._ui_frm)
        self._ui_settings = ttk.Checkbutton(self._ui_summary, style='Toolbutton')
        self._ui_settings_tip = Hovertip(self._ui_settings, text='')
        self._ui_start = ttk.Checkbutton(self._ui_summary, style='Toolbutton')
        self._ui_start_tip = Hovertip(self._ui_start, text='')
        self._ui_summary_lbl = ttk.Label(self._ui_summary)
        self._ui_preview = ttk.Checkbutton(self._ui_summary, style='Toolbutton')
        self._ui_preview_tip = Hovertip(self._ui_preview, text='')

        # Layout
        self._ui_settings.grid(column=0, row=0, sticky=tk.NW)
        self._ui_start.grid(column=1, row=0, sticky=tk.NW)
        self._ui_summary_lbl.grid(column=2, row=0, sticky=tk.EW)
        self._ui_preview.grid(column=3, row=0, sticky=tk.NW)
        self._ui_summary.columnconfigure(index=2, weight=1)

        self._ui_summary.grid(column=0, row=0, sticky=tk.EW)
        self._ui_frm.columnconfigure(index=0, weight=1)

        self._ui_frm.grid(column=0, row=0, sticky=tk.EW)
        self.columnconfigure(index=0, weight=1)

        # Padding
        self._model.grid_slaves_configure(self._ui_summary, padx=1, pady=1)
        self._model.grid_slaves_configure(self._ui_frm, padx=5, pady=(0, 5))
        self._ui_frm.configure(padding=0)

        # Texts & icons
        self._ui_frm_lbl.configure(text='Model & Filtering',
                                   image=self._model.icons.flt_stage,
                                   compound=tk.LEFT)
        self._ui_settings[IMAGE] = self._model.icons.settings
        self._ui_settings_tip.text = 'Edit filters'
        self._ui_start[IMAGE] = self._model.icons.start
        self._ui_start_tip.text = 'Proceed with filtering'
        self._ui_preview[IMAGE] = self._model.icons.preview
        self._ui_preview_tip.text = 'Preview filtered data'

        # Hooks
        self._ui_settings[COMMAND] = self._on_settings
        self._ui_start[COMMAND] = self._on_start
        self._ui_summary.bind(
            '<Configure>', lambda _e: self._ui_summary_lbl.configure(
                wraplength=self._ui_summary_lbl.winfo_width()))
        self._ui_preview[COMMAND] = self._on_preview

        # Data
        self._var_settings = tk.IntVar()
        self._ui_settings[VARIABLE] = self._var_settings
        self._var_start = tk.IntVar()
        self._ui_start[VARIABLE] = self._var_start
        self._var_summary = tk.StringVar()
        self._ui_summary_lbl[TEXTVARIABLE] = self._var_summary
        self._var_preview = tk.IntVar()
        self._ui_preview[VARIABLE] = self._var_preview

        self._update_thread: Optional[Thread] = None
        self._update_thread_err: Optional[str] = None
        self._update_thread_abort: Optional[mp.Event] = None

        self._settings_dlg: Optional[FilterCfgDialog] = None
        self._settings_apply: bool = False
        self._update_from_settings: bool = False

        # =0 ~ disabled, >0 ~ remaining flashes, None ~ infinite
        self._flash_counter = 0
        self._flash_id = None

        self.stage_ui_init()

    def stage_type(self):
        return self._stage_type

    def stage_type_next(self):
        return self._stage_type_next

    def stage_is_active(self) -> bool:
        lfm = self._model.lfm
        mla = self._model.mla
        lfl = self._model.lfl
        return lfm is not None and mla is not None and lfl is not None

    def stage_invalidate(self):
        self._flash_stop()

        if self._model.lfl is not None:
            self._model.lfl.reset_filtered_locs()

        if not self._update_from_settings:
            self._model.destroy_graph(GraphType.FILTERED)

        self._model.stage_enabled(self._stage_type, False)

        self.stage_ui_init()
        self._model.stage_invalidate(self._stage_type_next)

    def stage_start_update(self):
        self.stage_invalidate()
        self._model.stages_ui_updating(True)
        self.winfo_toplevel().configure(cursor='watch')

        self._ui_start[IMAGE] = self._model.icons.cancel
        self._ui_start_tip.text = 'Abort processing'
        self._ui_start.configure(state=tk.NORMAL)

        def _update_thread_fn():
            try:
                self._update_task()
            except BaseException as ex:
                self._update_thread_err = str(ex)
                tb.print_exception(None, ex, ex.__traceback__)

            def _update_done():
                self._ui_start[IMAGE] = self._model.icons.start
                self._ui_start_tip.text = 'Proceed with filtering'
                self._ui_start.configure(state=tk.DISABLED)

                self._update_thread = None
                self.winfo_toplevel().configure(cursor='')

                self._model.stages_ui_updating(False)

                # Reset the flag after the stage update prints it was aborted
                self._update_thread_abort = None

                if self._update_thread_err is not None:
                    err = self._update_thread_err
                    self._update_thread_err = None

                    messagebox.showerror(
                        title='Filtering Error',
                        message=f'The points cannot be filtered:\n{err}')

                    self._settings_apply = False
                    self._update_from_settings = False

                    self.stage_invalidate()
                    return

                if self._model.stage_is_active(self._stage_type_next):

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
        self._ui_update_done()

    def stage_ui_flash(self):
        self._flash_start()

    def stage_ui_updating(self, updating: bool):
        if updating:
            self._ui_update_start()
        else:
            self._ui_update_done()

    def _ui_update_start(self):
        self._ui_settings.configure(state=tk.DISABLED)
        if self._update_from_settings:
            settings_dlg = self._settings_dlg
            if settings_dlg is not None:
                settings_dlg.enable(False)
        self._ui_start.configure(state=tk.DISABLED)
        self._ui_preview.configure(state=tk.DISABLED)

    def _ui_update_done(self):
        self._ui_update_start()

        if self.stage_is_active():
            self._model.stage_enabled(self._stage_type, True)

            self._ui_settings.configure(state=tk.NORMAL)
            if self._update_from_settings:
                settings_dlg = self._settings_dlg
                if settings_dlg is not None:
                    settings_dlg.enable(True)
            self._ui_start.configure(state=tk.NORMAL)

            if self._model.stage_is_active(self._stage_type_next):
                self._ui_preview.configure(state=tk.NORMAL)
                locs = self._model.lfl.locs_2d.shape[0]
                count = locs - self._model.lfl.filtered_locs_2d.shape[0]
                self._var_summary.set(f'Filtered out {count} localisations')
            else:
                if (self._update_thread_abort is not None
                        and self._update_thread_abort.is_set()):
                    self._var_summary.set('Filtering aborted')
                else:
                    self._var_summary.set('No filtering done')
        else:
            self._var_summary.set('No filtering done yet')

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

    def _on_settings(self):
        cfg_dump_old = self._model.cfg.to_json()

        def _process_cb(apply: bool):
            self._settings_apply = apply
            self._update_from_settings = True
            nonlocal cfg_dump_old
            cfg_dump_new = self._model.cfg.to_json()
            if (cfg_dump_old != cfg_dump_new
                    or not self._model.stage_is_active(self._stage_type_next)):
                cfg_dump_old = cfg_dump_new
                self.stage_start_update()
            else:
                self._show_previews()
                self._settings_apply = False
                self._update_from_settings = False

        self._settings_dlg = FilterCfgDialog(self, self._model, process_cb=_process_cb)
        self._settings_dlg.show_modal()
        self._settings_dlg = None
        if not self._var_preview.get():
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
        if not self._model.stage_is_active(self._stage_type_next):
            return

        show = self._model.cfg.show_graphs and self._model.cfg.show_all_debug_graphs

        force_show = show or self._settings_apply
        force_update = force_update and self._model.graph_exists(GraphType.FILTERED)
        if force_show:
            self._var_preview.set(1)
        if force_show or force_update:
            self._on_preview(force_update)

    def _on_preview(self, force_update: bool = False):

        def draw(f: Figure, set_size: bool = True) -> Figure:
            return smlfm.graphs.draw_locs(
                f,
                xy=self._model.lfl.filtered_locs_2d[:, 3:5],
                lens_idx=self._model.lfl.filtered_locs_2d[:, 12],
                lens_centres=((self._model.mla.lens_centres - self._model.mla.centre)
                              * self._model.lfm.mla_to_xy_scale),
                # U,V values are around MLA centre but that offset is not included
                mla_centre=np.array([0.0, 0.0]),
                set_default_size=set_size)

        wnd = self._model.graphs[GraphType.FILTERED]
        if wnd is None:
            fig = draw(Figure())
            wnd = FigureWindow(fig, master=self,
                               title='Filtered localisations')
            wnd.bind('<Map>', func=lambda _evt: self._var_preview.set(1))
            wnd.bind('<Unmap>', func=lambda _evt: self._var_preview.set(0))
            self._model.graphs[GraphType.FILTERED] = wnd
        else:
            if force_update:
                draw(wnd.figure, set_size=False)
                wnd.refresh()

        if self._var_preview.get():
            wnd.deiconify()
        else:
            wnd.withdraw()

    # Executed on thread
    def _update_task(self):
        self._model.invoke_on_gui_thread_async(
            self._var_summary.set, 'Filtering...')
        tic = time.time()

        if self._model.cfg.filter_lenses:
            self._model.lfl.filter_lenses(self._model.mla, self._model.lfm)
        if self._model.cfg.filter_rhos is not None:
            self._model.lfl.filter_rhos(self._model.cfg.filter_rhos)
        if self._model.cfg.filter_spot_sizes is not None:
            self._model.lfl.filter_spot_sizes(self._model.cfg.filter_spot_sizes)
        if self._model.cfg.filter_photons is not None:
            self._model.lfl.filter_photons(self._model.cfg.filter_photons)

        self._model.lfl.init_alpha_uv(
            self._model.cfg.alpha_model,
            self._model.lfm,
            abort_event=self._update_thread_abort,
            worker_count=self._model.cfg.max_workers)

        if self._update_thread_abort is not None:
            if self._update_thread_abort.is_set():
                self._model.lfl.reset_filtered_locs()
                return

        if self._model.cfg.log_timing:
            print(f'Filtering and setting alpha model took'
                  f' {1e3 * (time.time() - tic):.3f} ms')

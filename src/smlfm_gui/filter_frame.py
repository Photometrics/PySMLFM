import multiprocessing as mp
import time
import tkinter as tk
import traceback as tb
from idlelib.tooltip import Hovertip
from threading import Thread
from tkinter import messagebox, ttk
from typing import Union

import numpy as np
from matplotlib.figure import Figure

import smlfm

from .app_model import AppModel, IStage
from .consts import *
from .figure_window import FigureWindow


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

        self._update_thread: Union[Thread, None] = None
        self._update_thread_err: Union[str, None] = None
        self._update_thread_abort: Union[mp.Event, None] = None

        # =0 ~ disabled, >0 ~ remaining flashes, None ~ infinite
        self._flash_counter = 0
        self._flash_id = None

        self.stage_ui_init()

    def stage_type(self):
        return self._stage_type

    def stage_type_next(self):
        return self._stage_type_next

    def stage_invalidate(self):
        self._flash_stop()

        if self._model.lfl is not None:
            self._model.lfl.reset_filtered_locs()
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

                    self.stage_invalidate()
                    return

                if self._model.lfl.alpha_model is not None:
                    if self._model.cfg.show_graphs:
                        if self._model.cfg.show_all_debug_graphs:
                            self._var_preview.set(1)
                            self._on_preview()

                    self._model.stage_ui_init(self._stage_type_next)
                    # Next phase updates automatically or the user continues manually
                    if self._model.cfg.confirm_mla_alignment:
                        self._model.stage_ui_flash(self._stage_type_next)
                    else:
                        self._model.stage_start_update(self._stage_type_next)

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
        self._ui_start.configure(state=tk.DISABLED)
        self._ui_preview.configure(state=tk.DISABLED)

    def _ui_update_done(self):
        self._ui_update_start()

        if self._model.lfl is not None:
            self._model.stage_enabled(self._stage_type, True)

            self._ui_settings.configure(state=tk.NORMAL)
            self._ui_start.configure(state=tk.NORMAL)

            if self._model.lfl.alpha_model is not None:
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
            self._var_summary.set('No filtering done')

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
        messagebox.showinfo(
            title='Notice',
            message='The settings UI is not implemented yet.')
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

    def _on_preview(self):
        wnd = self._model.graphs[GraphType.FILTERED]
        if wnd is None:
            fig = smlfm.graphs.draw_locs(
                Figure(),
                xy=self._model.lfl.filtered_locs_2d[:, 3:5],
                lens_idx=self._model.lfl.filtered_locs_2d[:, 12],
                lens_centres=((self._model.mla.lens_centres - self._model.mla.centre)
                              * self._model.lfm.mla_to_xy_scale),
                # U,V values are around MLA centre but that offset is not included
                mla_centre=np.array([0.0, 0.0]))
            wnd = FigureWindow(fig, master=self,
                               title='Filtered localisations')
            wnd.bind('<Map>', func=lambda _evt: self._var_preview.set(1))
            wnd.bind('<Unmap>', func=lambda _evt: self._var_preview.set(0))
            self._model.graphs[GraphType.FILTERED] = wnd

        if self._var_preview.get():
            wnd.deiconify()
        else:
            wnd.withdraw()

    # Executed on thread
    def _update_task(self):
        self._model.invoke_on_gui_thread_async(
            self._var_summary.set, 'Filtering...')
        tic = time.time()

        # TODO: Add variable number of filtering parameters to Config and GUI
        # self._model.lfl.filter_rhos([0.0, 0.8])
        # self._model.lfl.filter_spot_sizes([0.1, 1.0])
        # self._model.lfl.filter_photons([0.0, 500.0])

        self._model.lfl.init_alpha_uv(
            self._model.cfg.alpha_model,
            self._model.lfm,
            abort_event=self._update_thread_abort,
            worker_count=self._model.cfg.max_workers)

        if self._update_thread_abort is not None:
            if self._update_thread_abort.is_set():
                return

        if self._model.cfg.log_timing:
            print(f'Filtering and setting alpha model took'
                  f' {1e3 * (time.time() - tic):.3f} ms')
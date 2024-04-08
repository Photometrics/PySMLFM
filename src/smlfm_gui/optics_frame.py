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


class OpticsFrame(ttk.Frame, IStage):

    def __init__(self, master, model: AppModel, *args, **kwargs):
        super().__init__(master, *args, **kwargs)

        self._stage_type = StageType.OPTICS
        self._stage_type_next = StageType.FILTER

        self._model = model

        # Controls
        self._ui_frm_lbl = ttk.Label(self)
        self._ui_frm = ttk.LabelFrame(self, labelwidget=self._ui_frm_lbl)

        self._ui_summary = ttk.Frame(self._ui_frm)
        self._ui_settings = ttk.Checkbutton(self._ui_summary, style='Toolbutton')
        self._ui_settings_tip = Hovertip(self._ui_settings, text='')
        self._ui_summary_lbl = ttk.Label(self._ui_summary)
        self._ui_preview_mla = ttk.Checkbutton(self._ui_summary, style='Toolbutton')
        self._ui_preview_mla_tip = Hovertip(self._ui_preview_mla, text='')
        self._ui_preview = ttk.Checkbutton(self._ui_summary, style='Toolbutton')
        self._ui_preview_tip = Hovertip(self._ui_preview, text='')

        # Layout
        self._ui_settings.grid(column=0, row=0, sticky=tk.NW)
        self._ui_summary_lbl.grid(column=1, row=0, sticky=tk.EW)
        self._ui_preview_mla.grid(column=2, row=0, sticky=tk.NW)
        self._ui_preview.grid(column=3, row=0, sticky=tk.NW)
        self._ui_summary.columnconfigure(index=1, weight=1)

        self._ui_summary.grid(column=0, row=0, sticky=tk.EW)
        self._ui_frm.columnconfigure(index=0, weight=1)

        self._ui_frm.grid(column=0, row=0, sticky=tk.EW)
        self.columnconfigure(index=0, weight=1)

        # Padding
        self._model.grid_slaves_configure(self._ui_summary, padx=1, pady=1)
        self._model.grid_slaves_configure(self._ui_frm, padx=5, pady=(0, 5))
        self._ui_frm.configure(padding=0)

        # Texts & icons
        self._ui_frm_lbl.configure(text='Micro-Lens Array & Microscope',
                                   image=self._model.icons.opt_stage,
                                   compound=tk.LEFT)
        self._ui_settings[IMAGE] = self._model.icons.settings
        self._ui_settings_tip.text = 'Edit properties'
        self._ui_preview_mla[IMAGE] = self._model.icons.opt_dot
        self._ui_preview_mla_tip.text = 'Preview lens array'
        self._ui_preview[IMAGE] = self._model.icons.preview
        self._ui_preview_tip.text = 'Preview data mapping'

        # Hooks
        self._ui_settings[COMMAND] = self._on_settings
        self._ui_summary.bind(
            '<Configure>', lambda _e: self._ui_summary_lbl.configure(
                wraplength=self._ui_summary_lbl.winfo_width()))
        self._ui_preview_mla[COMMAND] = self._on_preview_mla
        self._ui_preview[COMMAND] = self._on_preview

        # Data
        self._var_settings = tk.IntVar()
        self._ui_settings[VARIABLE] = self._var_settings
        self._var_summary = tk.StringVar()
        self._ui_summary_lbl[TEXTVARIABLE] = self._var_summary
        self._var_preview_mla = tk.IntVar()
        self._ui_preview_mla[VARIABLE] = self._var_preview_mla
        self._var_preview = tk.IntVar()
        self._ui_preview[VARIABLE] = self._var_preview

        self._update_thread: Union[Thread, None] = None
        self._update_thread_err: Union[str, None] = None

        self.stage_ui_init()

    def stage_type(self):
        return self._stage_type

    def stage_type_next(self):
        return self._stage_type_next

    def stage_is_active(self) -> bool:
        csv = self._model.csv
        return csv is not None and csv.data is not None and csv.data.shape[0] > 0

    def stage_invalidate(self):
        self._model.lfm = None
        self._model.mla = None
        self._model.lfl = None
        for gt in [GraphType.MLA, GraphType.MAPPED]:
            self._model.destroy_graph(gt)

        self._model.stage_enabled(self._stage_type, False)

        self.stage_ui_init()
        self._model.stage_invalidate(self._stage_type_next)

    def stage_start_update(self):
        self.stage_invalidate()
        self._model.stages_ui_updating(True)
        self.winfo_toplevel().configure(cursor='watch')

        def _update_thread_fn():
            try:
                self._update_task()
            except BaseException as ex:
                self._update_thread_err = str(ex)
                tb.print_exception(None, ex, ex.__traceback__)

            def _update_done():
                self._update_thread = None
                self.winfo_toplevel().configure(cursor='')

                self._model.stages_ui_updating(False)

                if self._update_thread_err is not None:
                    err = self._update_thread_err
                    self._update_thread_err = None

                    messagebox.showerror(
                        title='Configuration Error',
                        message=f'The optics cannot be configured:\n{err}')

                    self.stage_invalidate()
                    return

                if self._model.stage_is_active(self._stage_type_next):
                    if self._model.cfg.show_graphs:
                        if self._model.cfg.show_all_debug_graphs:
                            self._var_preview_mla.set(1)
                            self._on_preview_mla()
                        if self._model.cfg.show_mla_alignment_graph:
                            self._var_preview.set(1)
                            self._on_preview()

                    self._model.stage_ui_init(self._stage_type_next)
                    # Next phase updates automatically or the user continues manually
                    if self._model.cfg.confirm_mla_alignment:
                        self._model.stage_ui_flash(self._stage_type_next)
                    else:
                        self._model.stage_start_update(self._stage_type_next)

                    if self._model.cfg.confirm_mla_alignment:
                        messagebox.showinfo(
                            title='Confirmation',
                            message='Check on the figure that the lenses are well'
                                    ' aligned with the data. If the alignment is'
                                    ' incorrect, adjust Micro-Lens Array parameters.\n'
                                    '\n'
                                    'Otherwise continue with flashing button.')

            self._model.invoke_on_gui_thread_async(_update_done)

        self._update_thread = Thread(target=_update_thread_fn, daemon=True)
        self._update_thread.start()

    def stage_ui_init(self):
        self._ui_update_done()

    def stage_ui_updating(self, updating: bool):
        if updating:
            self._ui_update_start()
        else:
            self._ui_update_done()

    def _ui_update_start(self):
        self._ui_settings.configure(state=tk.DISABLED)
        self._ui_preview_mla.configure(state=tk.DISABLED)
        self._ui_preview.configure(state=tk.DISABLED)

    def _ui_update_done(self):
        self._ui_update_start()

        if self.stage_is_active():
            self._model.stage_enabled(self._stage_type, True)

            self._ui_settings.configure(state=tk.NORMAL)

            if self._model.stage_is_active(self._stage_type_next):
                self._ui_preview_mla.configure(state=tk.NORMAL)

                if (self._model.mla.lattice_type
                        == smlfm.MicroLensArray.LatticeType.HEXAGONAL):
                    self._ui_preview_mla[IMAGE] = self._model.icons.opt_hexagon
                elif (self._model.mla.lattice_type
                      == smlfm.MicroLensArray.LatticeType.SQUARE):
                    self._ui_preview_mla[IMAGE] = self._model.icons.opt_square
                # elif (self._model.mla.lattice_type
                #       == smlfm.MicroLensArray.LatticeType.TRIANGULAR):
                #     self._ui_preview_mla[IMAGE] = self._model.icons.opt_triangle
                else:
                    self._ui_preview_mla[IMAGE] = self._model.icons.opt_dot

                if self._model.lfl is not None:
                    self._ui_preview.configure(state=tk.NORMAL)
                    lenses = np.unique(self._model.lfl.locs_2d[:, 12]).shape[0]
                    self._var_summary.set(f'Localisations mapped to {lenses} lenses')
                else:
                    self._var_summary.set('No localisations mapped to lenses')
            else:
                self._var_summary.set('No optics configured')
        else:
            self._var_summary.set('No optics configured yet')

    def _on_settings(self):
        messagebox.showinfo(
            title='Notice',
            message='The settings UI is not implemented yet.')
        self._var_settings.set(0)

    def _on_preview_mla(self):
        wnd = self._model.graphs[GraphType.MLA]
        if wnd is None:
            fig = smlfm.graphs.draw_mla(Figure(),
                                        self._model.mla.lens_centres,
                                        self._model.mla.centre)
            wnd = FigureWindow(fig, master=self,
                               title='Micro-lens array centres')
            wnd.bind('<Map>', func=lambda _evt: self._var_preview_mla.set(1))
            wnd.bind('<Unmap>', func=lambda _evt: self._var_preview_mla.set(0))
            self._model.graphs[GraphType.MLA] = wnd

        if self._var_preview_mla.get():
            wnd.deiconify()
        else:
            wnd.withdraw()

    def _on_preview(self):
        wnd = self._model.graphs[GraphType.MAPPED]
        if wnd is None:
            fig = smlfm.graphs.draw_locs(
                Figure(),
                xy=self._model.lfl.locs_2d[:, 3:5],
                lens_idx=self._model.lfl.locs_2d[:, 12],
                lens_centres=((self._model.mla.lens_centres - self._model.mla.centre)
                              * self._model.lfm.mla_to_xy_scale),
                # U,V values are around MLA centre but that offset is not included
                mla_centre=np.array([0.0, 0.0]))
            wnd = FigureWindow(fig, master=self,
                               title='Localisations with lens centers')
            wnd.bind('<Map>', func=lambda _evt: self._var_preview.set(1))
            wnd.bind('<Unmap>', func=lambda _evt: self._var_preview.set(0))
            self._model.graphs[GraphType.MAPPED] = wnd

        if self._var_preview.get():
            wnd.deiconify()
        else:
            wnd.withdraw()

    # Executed on thread
    def _update_task(self):
        self._model.invoke_on_gui_thread_async(
            self._var_summary.set, 'Configuring optics...')

        self._model.lfm = smlfm.FourierMicroscope(
            self._model.cfg.num_aperture,
            self._model.cfg.mla_lens_pitch,
            self._model.cfg.focal_length_mla,
            self._model.cfg.focal_length_obj_lens,
            self._model.cfg.focal_length_tube_lens,
            self._model.cfg.focal_length_fourier_lens,
            self._model.cfg.pixel_size_camera,
            self._model.cfg.ref_idx_immersion,
            self._model.cfg.ref_idx_medium)

        self._model.mla = smlfm.MicroLensArray(
            self._model.cfg.mla_type,
            self._model.cfg.focal_length_mla,
            self._model.cfg.mla_lens_pitch,
            self._model.cfg.mla_optic_size,
            self._model.cfg.mla_centre)

        self._model.mla.rotate_lattice(np.deg2rad(self._model.cfg.mla_rotation))
        self._model.mla.offset_lattice(
            self._model.cfg.mla_offset / self._model.lfm.mla_to_xy_scale)  # XY -> MLA

        self._model.invoke_on_gui_thread_async(
            self._var_summary.set, 'Mapping to lenses...')
        tic = time.time()

        self._model.csv.scale_peakfit_data(self._model.lfm.pixel_size_sample)
        locs_2d = self._model.csv.data.copy()

        # Center X and Y to their means
        # TODO: Why center the data to means? Ensure how is this related to MLA centre.
        locs_2d[:, 1] -= locs_2d[:, 1].mean()
        locs_2d[:, 2] -= locs_2d[:, 2].mean()

        self._model.lfl = smlfm.Localisations(locs_2d)
        self._model.lfl.assign_to_lenses(self._model.mla, self._model.lfm)

        if self._model.cfg.log_timing:
            print(f'Mapping points to lenses took'
                  f' {1e3 * (time.time() - tic):.3f} ms')

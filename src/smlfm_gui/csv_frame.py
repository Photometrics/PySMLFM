import time
import tkinter as tk
import traceback as tb
from idlelib.tooltip import Hovertip
from pathlib import Path
from threading import Thread
from tkinter import filedialog, messagebox, ttk
from typing import Union

import numpy as np
from matplotlib.figure import Figure

import smlfm

from .app_model import AppModel, IStage
from .consts import *
from .figure_window import FigureWindow


class CsvFrame(ttk.Frame, IStage):

    def __init__(self, master, model: AppModel, *args, **kwargs):
        super().__init__(master, *args, **kwargs)

        self._stage_type = StageType.CSV
        self._stage_type_next = StageType.OPTICS

        self._model = model

        # TODO: Add detection
        self._has_imagej = False

        # Controls
        self._ui_frm_lbl = ttk.Label(self)
        self._ui_frm = ttk.LabelFrame(self, labelwidget=self._ui_frm_lbl)

        self._ui_tabs = ttk.Notebook(self._ui_frm)

        self._ui_tab1 = ttk.Frame(self._ui_tabs)
        self._ui_tabs.add(self._ui_tab1)
        self._ui_file_loc_lbl = ttk.Label(self._ui_tab1)
        self._ui_file_loc = ttk.Entry(self._ui_tab1)
        self._ui_file_loc_btn = ttk.Button(self._ui_tab1)
        self._ui_fmt_loc_lbl = ttk.Label(self._ui_tab1)
        self._ui_fmt_loc = ttk.Combobox(self._ui_tab1, state=READONLY)
        self._ui_open = ttk.Button(self._ui_tab1)

        self._ui_tab2 = ttk.Frame(self._ui_tabs)
        self._ui_tabs.add(self._ui_tab2)
        if self._has_imagej:
            self._ui_file_img_lbl = ttk.Label(self._ui_tab2)
            self._ui_file_img = ttk.Entry(self._ui_tab2)
            self._ui_file_img_btn = ttk.Button(self._ui_tab2)
            self._ui_file_res_lbl = ttk.Label(self._ui_tab2)
            self._ui_file_res = ttk.Entry(self._ui_tab2, state=READONLY)
            self._ui_peakfit = ttk.Button(self._ui_tab2)
        else:
            self._ui_no_imagej_lbl = ttk.Label(self._ui_tab2)

        self._ui_summary = ttk.Frame(self._ui_frm)
        self._ui_summary_lbl = ttk.Label(self._ui_summary)
        self._ui_preview = ttk.Checkbutton(self._ui_summary, style='Toolbutton')
        self._ui_preview_tip = Hovertip(self._ui_preview, text='')

        # Layout
        self._ui_file_loc_lbl.grid(column=0, row=0, sticky=tk.E)
        self._ui_file_loc.grid(column=1, row=0, sticky=tk.EW)
        self._ui_file_loc_btn.grid(column=2, row=0, sticky=tk.W)
        self._ui_fmt_loc_lbl.grid(column=0, row=1, sticky=tk.E)
        self._ui_fmt_loc.grid(column=1, row=1, sticky=tk.EW, columnspan=2)
        self._ui_open.grid(column=1, row=2, sticky=tk.W)
        self._ui_tab1.columnconfigure(index=1, weight=1)

        if self._has_imagej:
            self._ui_file_img_lbl.grid(column=0, row=0, sticky=tk.E)
            self._ui_file_img.grid(column=1, row=0, sticky=tk.EW)
            self._ui_file_img_btn.grid(column=2, row=0, sticky=tk.W)
            self._ui_file_res_lbl.grid(column=0, row=1, sticky=tk.E)
            self._ui_file_res.grid(column=1, row=1, sticky=tk.EW, columnspan=2)
            self._ui_peakfit.grid(column=1, row=2, sticky=tk.W)
            self._ui_tab2.columnconfigure(index=1, weight=1)
        else:
            self._ui_no_imagej_lbl.grid(column=0, row=0, sticky=tk.NSEW)
            self._ui_tab2.columnconfigure(index=0, weight=1)
            self._ui_tab2.rowconfigure(index=0, weight=1)

        self._ui_tabs.columnconfigure(index=0, weight=1)

        self._ui_summary_lbl.grid(column=0, row=0, sticky=tk.EW)
        self._ui_preview.grid(column=1, row=0, sticky=tk.NW)
        self._ui_summary.columnconfigure(index=0, weight=1)

        self._ui_tabs.grid(column=0, row=0, sticky=tk.EW)
        self._ui_summary.grid(column=0, row=1, sticky=tk.EW)
        self._ui_frm.columnconfigure(index=0, weight=1)

        self._ui_frm.grid(column=0, row=0, sticky=tk.EW)
        self.columnconfigure(index=0, weight=1)

        # Padding
        self._model.grid_slaves_configure(self._ui_tab1, padx=1, pady=1)
        self._ui_tab1.configure(padding=5)
        self._model.grid_slaves_configure(self._ui_tab2, padx=1, pady=1)
        self._ui_tab2.configure(padding=5)
        self._ui_tabs.configure(padding=0)
        self._model.grid_slaves_configure(self._ui_summary, padx=1, pady=1)
        self._model.grid_slaves_configure(self._ui_frm, padx=5, pady=(0, 5))
        self._ui_frm.configure(padding=0)

        # Texts & icons
        self._ui_frm_lbl.configure(text='Localisations',
                                   image=self._model.icons.csv_stage,
                                   compound=tk.LEFT)
        self._ui_tabs.tab(self._ui_tab1,
                          text='I have CSV file',
                          image=self._model.icons.csv_data,
                          compound=tk.LEFT)
        self._ui_file_loc_lbl[TEXT] = 'Existing file:'
        self._ui_file_loc_btn.configure(text='...', width=3)
        self._ui_fmt_loc_lbl[TEXT] = 'File format:'
        self._ui_open.configure(text='Open',
                                image=self._model.icons.open,
                                compound=tk.LEFT)
        self._ui_tabs.tab(self._ui_tab2,
                          text='I have image stack only',
                          image=self._model.icons.csv_stack,
                          compound=tk.LEFT)
        if self._has_imagej:
            self._ui_file_img_lbl[TEXT] = 'Image stack:'
            self._ui_file_img_btn.configure(text='...', width=3)
            self._ui_file_res_lbl[TEXT] = 'Result file:'
            self._ui_peakfit.configure(text='Run PeakFit in ImageJ',
                                       image=self._model.icons.csv_peakfit,
                                       compound=tk.LEFT)
        else:
            # TODO: Change the text once ImageJ detection implemented
            self._ui_no_imagej_lbl.configure(text='ImageJ detection not implemented yet',
                                             anchor=tk.CENTER)
            # self._ui_no_imagej_lbl.configure(text='ImageJ not detected',
            #                                  anchor=tk.CENTER)
        self._ui_preview[IMAGE] = self._model.icons.preview
        self._ui_preview_tip.text = 'Preview raw localisations'

        # Hooks
        self._ui_file_loc.bind(
            '<FocusOut>', lambda _e: self._on_file_loc_leave())
        self._ui_file_loc_btn[COMMAND] = self._on_get_file_loc
        self._ui_open[COMMAND] = self._on_open
        if self._has_imagej:
            self._ui_file_img_btn[COMMAND] = self._on_get_file_img
            self._ui_peakfit[COMMAND] = self._on_run_peakfit
        self._ui_summary.bind(
            '<Configure>', lambda _e: self._ui_summary_lbl.configure(
                wraplength=self._ui_summary_lbl.winfo_width()))
        self._ui_preview[COMMAND] = self._on_preview

        # Data
        self._var_file_loc = tk.StringVar()
        self._ui_file_loc[TEXTVARIABLE] = self._var_file_loc
        self._var_fmt_loc = tk.StringVar()
        self._ui_fmt_loc.configure(
            textvariable=self._var_fmt_loc,
            values=[f.name for f in smlfm.LocalisationFile.Format])
        self._var_file_img = tk.StringVar()
        self._var_file_res = tk.StringVar()
        if self._has_imagej:
            self._ui_file_img[TEXTVARIABLE] = self._var_file_img
            self._ui_file_res[TEXTVARIABLE] = self._var_file_res
        self._var_summary = tk.StringVar()
        self._ui_summary_lbl[TEXTVARIABLE] = self._var_summary
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
        return self._model.cfg is not None

    def stage_invalidate(self):
        self._model.csv = None
        self._model.destroy_graph(GraphType.CSV_RAW)

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
                        title='File Error',
                        message=f'The localisations cannot be loaded:\n{str(err)}',
                        detail=self._model.cfg.csv_file)

                    self.stage_invalidate()
                    return

                if self._model.stage_is_active(self._stage_type_next):
                    if self._model.cfg.show_graphs:
                        if self._model.cfg.show_all_debug_graphs:
                            self._var_preview.set(1)
                            self._on_preview()

                    self._model.stage_ui_init(self._stage_type_next)
                    self._model.stage_start_update(self._stage_type_next)

            self._model.invoke_on_gui_thread_async(_update_done)

        self._update_thread = Thread(target=_update_thread_fn, daemon=True)
        self._update_thread.start()

    def stage_ui_init(self):
        if self._model.cfg is not None:
            if self._model.cfg.csv_file is not None:
                self._var_file_loc.set(str(self._model.cfg.csv_file))
            self._var_fmt_loc.set(self._model.cfg.csv_format.name)

        self._ui_update_done()

    def stage_ui_updating(self, updating: bool):
        if updating:
            self._ui_update_start()
        else:
            self._ui_update_done()

    def _ui_update_start(self):
        self._ui_file_loc.configure(state=tk.DISABLED)
        self._ui_file_loc_btn.configure(state=tk.DISABLED)
        self._ui_fmt_loc.configure(state=tk.DISABLED)
        self._ui_open.configure(state=tk.DISABLED)
        if self._has_imagej:
            self._ui_file_img.configure(state=tk.DISABLED)
            self._ui_file_img_btn.configure(state=tk.DISABLED)
            self._ui_peakfit.configure(state=tk.DISABLED)

        self._ui_preview.configure(state=tk.DISABLED)

    def _ui_update_done(self):
        self._ui_update_start()

        if self.stage_is_active():
            self._model.stage_enabled(self._stage_type, True)

            self._ui_file_loc.configure(state=tk.NORMAL)
            self._ui_file_loc_btn.configure(state=tk.NORMAL)
            self._ui_fmt_loc.configure(state=READONLY)
            self._ui_open.configure(state=tk.NORMAL)
            if self._has_imagej:
                self._ui_file_img.configure(state=tk.NORMAL)
                self._ui_file_img_btn.configure(state=tk.NORMAL)
                self._ui_peakfit.configure(state=tk.NORMAL)

            if self._model.stage_is_active(self._stage_type_next):
                self._ui_preview.configure(state=tk.NORMAL)
                locs = self._model.csv.data.shape[0]
                frames = np.unique(self._model.csv.data[:, 0]).shape[0]
                self._var_summary.set(
                    f'Loaded {locs} localisations from {frames} unique frames')
            else:
                self._var_summary.set('No localisations loaded')
        else:
            self._var_summary.set('No localisations loaded yet')

    def _on_file_loc_leave(self):
        file_name = self._var_file_loc.get()
        self._model.cfg.csv_file = Path(file_name) if file_name else None

    def _on_get_file_loc(self):
        initial_dir = None
        initial_file = None
        if self._model.cfg.csv_file is not None:
            initial_dir = self._model.cfg.csv_file.parent
            initial_file = self._model.cfg.csv_file.name

        file_name = filedialog.askopenfilename(
            parent=self,
            title='Select CSV file to open...',
            filetypes=(('CSV files', '*.csv'), ('All files', '*')),
            initialdir=initial_dir,
            initialfile=initial_file)
        if file_name:
            self._var_file_loc.set(file_name)
            self._model.cfg.csv_file = Path(file_name)

    def _on_get_file_img(self):
        initial_dir = None
        initial_file = None
        file_name = self._var_file_img.get()
        if file_name:
            path = Path(file_name)
            initial_dir = path.parent
            initial_file = path.name
        else:
            if self._model.cfg.csv_file is not None:
                initial_dir = self._model.cfg.csv_file.parent

        file_name = filedialog.askopenfilename(
            parent=self,
            title='Select image stack file to open...',
            filetypes=(('TIFF files', '*.tiff *.tif'), ('All files', '*')),
            initialdir=initial_dir,
            initialfile=initial_file)
        if file_name:
            self._var_file_img.set(file_name)
            csv_file = Path(file_name + '.csv')
            self._var_file_res.set(str(csv_file))
            self._var_file_loc.set(str(csv_file))
            self._model.cfg.csv_file = csv_file

    def _on_open(self):
        if self._model.cfg.csv_file is None:
            messagebox.showerror(
                title='File Error',
                message='The CSV file path cannot be empty.')
            return

        if not self._model.cfg.csv_file.exists():
            messagebox.showerror(
                title='File Error',
                message='The CSV file does not exist:',
                detail=self._model.cfg.csv_file)
            return

        self.stage_start_update()

    def _on_preview(self):
        wnd = self._model.graphs[GraphType.CSV_RAW]
        if wnd is None:
            fig = smlfm.graphs.draw_locs_csv(Figure(), self._model.csv.data[:, 1:3])
            wnd = FigureWindow(fig, master=self, title='Raw localisations')
            wnd.bind('<Map>', func=lambda _evt: self._var_preview.set(1))
            wnd.bind('<Unmap>', func=lambda _evt: self._var_preview.set(0))
            self._model.graphs[GraphType.CSV_RAW] = wnd

        if self._var_preview.get():
            wnd.deiconify()
        else:
            wnd.withdraw()

    def _on_run_peakfit(self):
        # TODO: _ui_peakfit - validate paths and run PeakFit.
        #       When returned without error call self.stage_start_update()
        #       Does PeakFit plugin block the the UI?
        # file_name = self._var_file_img.get()
        pass

    # Executed on thread
    def _update_task(self):
        self._model.invoke_on_gui_thread_async(
            self._var_summary.set, 'Loading localisations...')
        tic = time.time()

        self._model.csv = smlfm.LocalisationFile(
            self._model.cfg.csv_file, self._model.cfg.csv_format)
        self._model.csv.read()

        if self._model.cfg.log_timing:
            print(f'Loading {repr(self._model.cfg.csv_file.name)} took'
                  f' {1e3 * (time.time() - tic):.3f} ms')

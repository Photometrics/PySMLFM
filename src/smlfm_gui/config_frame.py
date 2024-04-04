import pkgutil
import tkinter as tk
import traceback as tb
from idlelib.tooltip import Hovertip
from pathlib import Path
from threading import Thread
from tkinter import filedialog, messagebox, ttk
from typing import Union

import smlfm

from .app_model import AppModel, IStage
from .consts import *


class ConfigFrame(ttk.Frame, IStage):

    def __init__(self, master, model: AppModel, *args, **kwargs):
        super().__init__(master, *args, **kwargs)

        self._stage_type = StageType.CONFIG
        self._stage_type_next = StageType.CSV

        self._model = model

        # Controls
        self._ui_frm_lbl = ttk.Label(self)
        self._ui_frm = ttk.LabelFrame(self, labelwidget=self._ui_frm_lbl)

        self._ui_tab = ttk.Frame(self._ui_frm)
        self._ui_file_lbl = ttk.Label(self._ui_tab)
        self._ui_file = ttk.Entry(self._ui_tab)
        self._ui_file_tip = Hovertip(self._ui_file, text='')
        self._ui_file_btn = ttk.Button(self._ui_tab)

        self._ui_buttons = ttk.Frame(self._ui_tab)
        self._ui_open = ttk.Button(self._ui_buttons)
        self._ui_save_as = ttk.Button(self._ui_buttons)

        self._ui_summary = ttk.Frame(self._ui_frm)
        self._ui_settings = ttk.Checkbutton(self._ui_summary, style='Toolbutton')
        self._ui_settings_tip = Hovertip(self._ui_settings, text='')
        self._ui_summary_lbl = ttk.Label(self._ui_summary)

        # Layout
        self._ui_open.grid(column=0, row=0, sticky=tk.W)
        self._ui_save_as.grid(column=2, row=0, sticky=tk.W)
        # self._ui_buttons.columnconfigure(index=3, weight=1)

        self._ui_file_lbl.grid(column=0, row=0, sticky=tk.E)
        self._ui_file.grid(column=1, row=0, sticky=tk.EW)
        self._ui_file_btn.grid(column=2, row=0, sticky=tk.W)
        self._ui_buttons.grid(column=1, row=1, sticky=tk.EW, columnspan=2)
        self._ui_tab.columnconfigure(index=1, weight=1)

        self._ui_settings.grid(column=0, row=0, sticky=tk.NW)
        self._ui_summary_lbl.grid(column=1, row=0, sticky=tk.EW)
        self._ui_summary.columnconfigure(index=1, weight=1)

        self._ui_tab.grid(column=0, row=0, sticky=tk.EW)
        self._ui_summary.grid(column=0, row=1, sticky=tk.EW)
        self._ui_frm.columnconfigure(index=0, weight=1)

        self._ui_frm.grid(column=0, row=0, sticky=tk.EW)
        self.columnconfigure(index=0, weight=1)

        # Padding
        self._model.grid_slaves_configure(self._ui_tab, padx=1, pady=1)
        self._ui_tab.configure(padding=0)
        self._model.grid_slaves_configure(self._ui_buttons, padx=1, pady=1)
        self._ui_buttons.configure(padding=0)
        self._model.grid_slaves_configure(self._ui_summary, padx=1, pady=1)
        self._model.grid_slaves_configure(self._ui_frm, padx=5, pady=(0, 5))
        self._ui_frm.configure(padding=0)

        # Texts & icons
        self._ui_frm_lbl.configure(text='Configuration',
                                   image=self._model.icons.cfg_stage,
                                   compound=tk.LEFT)
        self._ui_file_lbl[TEXT] = 'Existing file:'
        self._ui_file_tip.text = 'Use empty string to load default configuration'
        self._ui_file_btn.configure(text='...', width=3)
        self._ui_open.configure(text='Open',
                                image=self._model.icons.open,
                                compound=tk.LEFT)
        self._ui_save_as.configure(text='Save as',
                                   image=self._model.icons.save_as,
                                   compound=tk.LEFT)
        self._ui_settings[IMAGE] = self._model.icons.settings
        self._ui_settings_tip.text = 'Edit extra settings'

        # Hooks
        self._ui_file.bind(
            '<FocusOut>', lambda _e: self._on_file_leave())
        self._ui_file_btn[COMMAND] = self._on_get_file
        self._ui_open[COMMAND] = self._on_open
        self._ui_save_as[COMMAND] = self._on_save_as
        self._ui_settings[COMMAND] = self._on_settings
        self._ui_summary.bind(
            '<Configure>', lambda _e: self._ui_summary_lbl.configure(
                wraplength=self._ui_summary_lbl.winfo_width()))

        # Data
        self._var_file = tk.StringVar()
        self._ui_file[TEXTVARIABLE] = self._var_file
        self._var_settings = tk.IntVar()
        self._ui_settings[VARIABLE] = self._var_settings
        self._var_summary = tk.StringVar()
        self._ui_summary_lbl[TEXTVARIABLE] = self._var_summary

        self._update_thread: Union[Thread, None] = None
        self._update_thread_err: Union[str, None] = None

        self.stage_ui_init()

    def stage_type(self):
        return self._stage_type

    def stage_type_next(self):
        return self._stage_type_next

    def stage_invalidate(self):
        self._model.cfg = None

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

                    detail = self._model.cfg_file
                    if self._model.cfg_file is None:
                        detail = '<default>'
                    messagebox.showerror(
                        title='File Error',
                        message=f'The configuration cannot be loaded:\n{err}',
                        detail=detail)

                    self.stage_invalidate()
                    return

                self._model.stage_ui_init(self._stage_type_next)
                self._model.stage_start_update(self._stage_type_next)

            self._model.invoke_on_gui_thread_async(_update_done)

        self._update_thread = Thread(target=_update_thread_fn, daemon=True)
        self._update_thread.start()

    def stage_ui_init(self):
        if self._model.cfg_file is not None:
            self._var_file.set(str(self._model.cfg_file))
        else:
            if self._model.cli_overrides:
                if self._model.cli_cfg_file is not None:
                    self._model.cfg_file = self._model.cli_cfg_file
                    self._var_file.set(str(self._model.cfg_file))

        self._ui_update_done()

    def stage_ui_updating(self, updating: bool):
        if updating:
            self._ui_update_start()
        else:
            self._ui_update_done()

    def _ui_update_start(self):
        self._ui_file.configure(state=tk.DISABLED)
        self._ui_file_btn.configure(state=tk.DISABLED)
        self._ui_open.configure(state=tk.DISABLED)
        self._ui_save_as.configure(state=tk.DISABLED)

    def _ui_update_done(self):
        self._ui_update_start()

        self._model.stage_enabled(self._stage_type, True)

        self._ui_file.configure(state=tk.NORMAL)
        self._ui_file_btn.configure(state=tk.NORMAL)
        self._ui_open.configure(state=tk.NORMAL)

        if self._model.cfg is not None:
            self._ui_save_as.configure(state=tk.NORMAL)
            if self._model.cfg_file:
                self._var_summary.set(f'Loaded configuration from'
                                      f' {self._model.cfg_file.name}')
            else:
                self._var_summary.set('Loaded default configuration')
        else:
            self._var_summary.set('No configuration loaded')

    def _on_file_leave(self):
        file_name = self._var_file.get()
        self._model.cfg_file = Path(file_name) if file_name else None

    def _on_get_file(self):
        initial_dir = None
        initial_file = None
        if self._model.cfg_file is not None:
            initial_dir = self._model.cfg_file.parent
            initial_file = self._model.cfg_file.name

        file_name = filedialog.askopenfilename(
            parent=self,
            title='Select configuration file to open...',
            filetypes=(('JSON files', '*.json'), ('All files', '*')),
            initialdir=initial_dir,
            initialfile=initial_file)
        if file_name:
            self._var_file.set(file_name)
            self._model.cfg_file = Path(file_name)

    def _on_open(self):
        if self._model.cfg_file is not None:
            if not self._model.cfg_file.exists():
                messagebox.showerror(
                    title='File Error',
                    message='The configuration file does not exist.\n'
                            'Delete the path to load default configuration.',
                    detail=self._model.cfg_file)
                return

        self.stage_start_update()

    def _on_save_as(self):
        initial_dir = None
        initial_file = None
        if self._model.cfg_file is not None:
            path = self._model.cfg_file
            initial_dir = path.parent
            initial_file = path.name

        file_name = filedialog.asksaveasfilename(
            parent=self,
            title='Save configuration as...',
            filetypes=(('JSON files', '*.json'), ('All files', '*')),
            initialdir=initial_dir,
            initialfile=initial_file)
        if file_name:
            self._var_file.set(file_name)
            self._model.cfg_file = Path(file_name)
            self.save(self._model.cfg_file)

    def save(self, file_name: Path):
        try:
            cfg_dump = self._model.cfg.to_json()
            with open(file_name, 'wt') as file:
                file.write(cfg_dump)
        except BaseException as ex:
            messagebox.showerror(
                title='File Error',
                message=f'The configuration cannot be saved:\n{str(ex)}',
                detail=file_name)

    def _on_settings(self):
        messagebox.showinfo(
            title='Notice',
            message='The settings UI is not implemented yet.')
        self._var_settings.set(0)

    # Executed on thread
    def _update_task(self):
        self._model.invoke_on_gui_thread_async(
            self._var_summary.set, 'Loading configuration...')

        # CLI option takes precedence
        if self._model.cli_overrides:
            if self._model.cli_cfg_file is not None:
                self._model.cfg_file = self._model.cli_cfg_file

        if self._model.cfg_file is not None:
            with open(self._model.cfg_file, 'rt') as file:
                cfg_dump = file.read()
        else:
            cfg_dump = pkgutil.get_data(
                smlfm.__name__, 'data/default-config.json').decode()

        self._model.cfg = smlfm.Config.from_json(cfg_dump)

        # CLI option takes precedence
        if self._model.cli_overrides or self._model.cfg.csv_file is None:
            if self._model.cli_csv_file is not None:
                self._model.cfg.csv_file = self._model.cli_csv_file

        # Uncomment to override
        # self._model.cfg.mla_centre = np.array([np.sqrt(3.0) / 2, 0.5])
        # self._model.cfg.mla_centre = np.array([np.sqrt(3.0), 1.0])
        # self._model.cfg.mla_centre = np.array([0.0, 1.0])
        # self._model.cfg.mla_centre = np.array([np.sqrt(3.0), 2.0])

        # Uncomment to override
        # self._model.cfg.mla_offset = np.array([-7.1, 1.0])

        # Uncomment to override
        # self._model.cfg.save_dir = None

        # Uncomment to override
        # self._model.cfg.confirm_mla_alignment = False

        self._model.cli_overrides = False

import os
import tkinter as tk
from idlelib.tooltip import Hovertip
from pathlib import Path
from tkinter import filedialog, ttk
from typing import Callable, Optional

from .app_model import AppModel
from .cfg_dialog import CfgDialog


class ConfigCfgDialog(CfgDialog):

    def __init__(self, parent, model: AppModel, title: Optional[str] = None,
                 process_cb: Optional[Callable[[bool], None]] = None):
        if title is None:
            title = 'Common Settings'

        self._ui_fiji_dir: Optional[ttk.Entry] = None
        fiji_dir_name = '' if model.cfg.fiji_dir is None else str(model.cfg.fiji_dir)
        self._var_fiji_dir = tk.StringVar(value=fiji_dir_name)
        self._ui_fiji_dir_tip: Optional[Hovertip] = None

        self._ui_jvm_opts: Optional[ttk.Entry] = None
        self._var_jvm_opts = tk.StringVar(value=model.cfg.fiji_jvm_opts)

        self._ui_show_graphs: Optional[ttk.Checkbutton] = None
        self._var_show_graphs = tk.BooleanVar(value=model.cfg.show_graphs)

        self._ui_show_result_graphs: Optional[ttk.Checkbutton] = None
        self._var_show_result_graphs = tk.BooleanVar(
            value=model.cfg.show_result_graphs)

        self._ui_show_mla_alignment_graph: Optional[ttk.Checkbutton] = None
        self._var_show_mla_alignment_graph = tk.BooleanVar(
            value=model.cfg.show_mla_alignment_graph)

        self._ui_show_all_debug_graphs: Optional[ttk.Checkbutton] = None
        self._var_show_all_debug_graphs = tk.BooleanVar(
            value=model.cfg.show_all_debug_graphs)

        self._ui_confirm_mla_alignment: Optional[ttk.Checkbutton] = None
        self._var_confirm_mla_alignment = tk.BooleanVar(
            value=model.cfg.confirm_mla_alignment)

        self._ui_log_timing: Optional[ttk.Checkbutton] = None
        self._var_log_timing = tk.BooleanVar(value=model.cfg.log_timing)

        self._ui_max_workers: Optional[ttk.Entry] = None
        self._var_max_workers = tk.StringVar(value=str(model.cfg.max_workers))
        self._ui_max_workers_tip: Optional[Hovertip] = None

        super().__init__(parent, model, title, process_cb=process_cb)

    # noinspection PyProtectedMember
    # pylint: disable=protected-access
    def body(self, master) -> tk.BaseWidget:
        ui_tab = ttk.Frame(master)
        row = 0

        ui_fiji_dir_lbl = ttk.Label(ui_tab, text='Fiji folder:', anchor=tk.E)
        Hovertip(ui_fiji_dir_lbl, text=self.model.cfg._fiji_dir_doc)
        self._ui_fiji_dir = ttk.Entry(ui_tab, textvariable=self._var_fiji_dir)
        self._ui_fiji_dir_tip = Hovertip(
            self._ui_fiji_dir, text=self.model.cfg._fiji_dir_doc)
        ui_fiji_dir_btn = ttk.Button(
            ui_tab, text='...', width=3,
            command=self._on_get_fiji_dir)
        self.ui_widgets.append(self._ui_fiji_dir)
        self.ui_widgets.append(ui_fiji_dir_btn)
        #
        ui_fiji_dir_lbl.grid(column=0, row=row, sticky=tk.EW)
        self._ui_fiji_dir.grid(column=1, row=row, sticky=tk.EW)
        ui_fiji_dir_btn.grid(column=2, row=row, sticky=tk.W)
        row += 1

        ui_jvm_opts_lbl = ttk.Label(ui_tab, text='JVM options:', anchor=tk.E)
        Hovertip(ui_jvm_opts_lbl, text=self.model.cfg._fiji_jvm_opts_doc)
        self._ui_jvm_opts = ttk.Entry(ui_tab, textvariable=self._var_jvm_opts)
        Hovertip(self._ui_jvm_opts, text=self.model.cfg._fiji_jvm_opts_doc)
        self.ui_widgets.append(self._ui_jvm_opts)
        #
        ui_jvm_opts_lbl.grid(column=0, row=row, sticky=tk.EW)
        self._ui_jvm_opts.grid(column=1, row=row, sticky=tk.EW)
        row += 1

        self._ui_show_graphs = ttk.Checkbutton(
            ui_tab, onvalue=True, offvalue=False,
            text='Show graphs',
            variable=self._var_show_graphs)
        Hovertip(self._ui_show_graphs, text=self.model.cfg._show_graphs_doc)
        self.ui_widgets.append(self._ui_show_graphs)
        #
        self._ui_show_graphs.grid(column=0, row=row, sticky=tk.EW, columnspan=2)
        row += 1

        self._ui_show_result_graphs = ttk.Checkbutton(
            ui_tab, onvalue=True, offvalue=False,
            text='Show result graphs',
            variable=self._var_show_result_graphs)
        Hovertip(self._ui_show_result_graphs,
                 text=self.model.cfg._show_result_graphs_doc)
        self.ui_widgets.append(self._ui_show_result_graphs)
        #
        self._ui_show_result_graphs.grid(
            column=0, row=row, sticky=tk.EW, columnspan=2)
        row += 1

        self._ui_show_mla_alignment_graph = ttk.Checkbutton(
            ui_tab, onvalue=True, offvalue=False,
            text='Show MLA alignment',
            variable=self._var_show_mla_alignment_graph)
        Hovertip(self._ui_show_mla_alignment_graph,
                 text=self.model.cfg._show_mla_alignment_graph_doc)
        self.ui_widgets.append(self._ui_show_mla_alignment_graph)
        #
        self._ui_show_mla_alignment_graph.grid(
            column=0, row=row, sticky=tk.EW, columnspan=2)
        row += 1

        self._ui_show_all_debug_graphs = ttk.Checkbutton(
            ui_tab, onvalue=True, offvalue=False,
            text='Show all intermediate graphs',
            variable=self._var_show_all_debug_graphs)
        Hovertip(self._ui_show_all_debug_graphs,
                 text=self.model.cfg._show_all_debug_graphs_doc)
        self.ui_widgets.append(self._ui_show_all_debug_graphs)
        #
        self._ui_show_all_debug_graphs.grid(
            column=0, row=row, sticky=tk.EW, columnspan=2)
        row += 1

        self._ui_confirm_mla_alignment = ttk.Checkbutton(
            ui_tab, onvalue=True, offvalue=False,
            text='Confirm MLA alignment',
            variable=self._var_confirm_mla_alignment)
        Hovertip(self._ui_confirm_mla_alignment,
                 text=self.model.cfg._confirm_mla_alignment_doc)
        self.ui_widgets.append(self._ui_confirm_mla_alignment)
        #
        self._ui_confirm_mla_alignment.grid(
            column=0, row=row, sticky=tk.EW, columnspan=2)
        row += 1

        self._ui_log_timing = ttk.Checkbutton(
            ui_tab, onvalue=True, offvalue=False,
            text='Log timing to console',
            variable=self._var_log_timing)
        Hovertip(self._ui_log_timing, text=self.model.cfg._log_timing_doc)
        self.ui_widgets.append(self._ui_log_timing)
        #
        self._ui_log_timing.grid(column=0, row=row, sticky=tk.EW, columnspan=2)
        row += 1

        max_cpu = os.cpu_count()
        limits = ('\n\nCPU count not detected.' if max_cpu is None else
                  f'\n\nDetected CPU count: {max_cpu}')
        #
        ui_max_workers_lbl = ttk.Label(ui_tab, text='Max. workers:', anchor=tk.E)
        Hovertip(ui_max_workers_lbl, text=self.model.cfg._max_workers_doc + limits)
        self._ui_max_workers = ttk.Spinbox(
            ui_tab, from_=0, to=os.cpu_count(), increment=1, format='%.0f',
            textvariable=self._var_max_workers)
        self._ui_max_workers_tip = Hovertip(
            self._ui_max_workers, text=self.model.cfg._max_workers_doc)
        self.ui_widgets.append(self._ui_max_workers)
        #
        ui_max_workers_lbl.grid(column=0, row=row, sticky=tk.EW)
        self._ui_max_workers.grid(column=1, row=row, sticky=tk.EW)
        row += 1

        # Final padding and layout
        ui_tab.columnconfigure(index=1, weight=1)
        self.model.grid_slaves_configure(ui_tab, padx=1, pady=1)

        ui_tab.pack(anchor=tk.NW, fill=tk.X, expand=True, padx=5, pady=5)

        return self._ui_fiji_dir  # Control that gets initial focus

    def _on_get_fiji_dir(self) -> None:
        dir_name = filedialog.askdirectory(
            parent=self,
            title='Select Fiji.app folder...',
            initialdir=self._var_fiji_dir.get())
        if dir_name:
            self._var_fiji_dir.set(dir_name)

    def validate(self) -> bool:
        fiji_dir = Path(self._var_fiji_dir.get())
        if not fiji_dir.exists() or not fiji_dir.is_dir():
            self.initial_focus = self._ui_fiji_dir
            self._ui_fiji_dir_tip.showtip()
            return False
        if not self.is_int(self._var_max_workers.get()):
            self.initial_focus = self._ui_max_workers
            self._ui_max_workers_tip.showtip()
            return False

        return super().validate()

    def process(self) -> None:
        self.model.cfg.fiji_dir = Path(self._var_fiji_dir.get())
        self.model.cfg.fiji_jvm_opts = self._var_jvm_opts.get()
        self.model.cfg.show_graphs = self._var_show_graphs.get()
        self.model.cfg.show_result_graphs = self._var_show_result_graphs.get()
        self.model.cfg.show_mla_alignment_graph = self._var_show_mla_alignment_graph.get()
        self.model.cfg.show_all_debug_graphs = self._var_show_all_debug_graphs.get()
        self.model.cfg.confirm_mla_alignment = self._var_confirm_mla_alignment.get()
        self.model.cfg.log_timing = self._var_log_timing.get()
        self.model.cfg.max_workers = self.clamp(
            int(self._var_max_workers.get()), 0, os.cpu_count())

        super().process()

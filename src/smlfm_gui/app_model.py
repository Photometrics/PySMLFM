import sys
import threading
import tkinter as tk
from pathlib import Path
from queue import Empty, SimpleQueue
from tkinter import ttk
from typing import Dict, Optional

import numpy.typing as npt

import smlfm

from .assets import Icons
from .consts import GraphType, StageType
from .figure_window import FigureWindow


class IStage:
    def stage_type(self) -> StageType:
        """Returns the stage type."""
        raise NotImplementedError('Subclass must implement this')

    def stage_type_next(self) -> Optional[StageType]:
        """Returns the next stage type."""
        raise NotImplementedError('Subclass must implement this')

    def stage_is_active(self) -> bool:
        """Returns the stage state, True when the stage has valid input."""
        raise NotImplementedError('Subclass must implement this')

    def stage_invalidate(self):
        """Invalidates the stage data."""
        raise NotImplementedError('Subclass must implement this')

    def stage_start_update(self):
        """Starts the stage data update, load resources, etc."""
        raise NotImplementedError('Subclass must implement this')

    def stage_ui_init(self):
        """Initializes the stage UI, possibly with date from previous stages."""
        raise NotImplementedError('Subclass must implement this')

    def stage_ui_flash(self):
        """Flashes with a control where the user should continue, no-op by default."""

    def stage_ui_updating(self, updating: bool):
        """Changes the stage UI state. If `updating` is True the UI is mostly
        disabled, except some 'Cancel' or 'Abort' button if exists.
        If the update is not in progress, the UI reflects internal state and
        enables UI controls that have valid input data from model."""
        raise NotImplementedError('Subclass must implement this')


# pylint: disable=too-many-instance-attributes
class AppModel:
    """A class holding application data and guards top-level logic.

    The UI and logic is split into multiple stages that build a chain.
    Invalidating first stage invalidates all other stages.
    Invalidating last stage invalidates last stage only.

    Most of the stages have input data stored in the 'cfg' member, some of them
    can visualize the output in a graph.

    The stages have the following order:
        1. CONFIG stage - Configuration
            - Invalidate:
                - Deletes `cfg`
                - Invalidates CSV stage
            - Update:
                - Creates `cfg` (from JSON file)
                - Updates CSV stage
        2. CSV stage - Localisations
            - Invalidate:
                - Deletes `csv`
                - Deletes CSV_RAW graph
                - Invalidates OPTICS stage
            - Update:
                - Creates `csv` (from CSV file and `cfg`)
                - Updates CSV_RAW graph data
                - Updates OPTICS stage
        3. OPTICS stage - Micro-Lens Array & Microscope
            - Invalidate:
                - Deletes `mla`, `lfm` and `lfl`
                - Deletes MLA and MAPPED graphs
                - Invalidates FILTER stage
            - Update:
                - Creates `lfm` and `mla` (from `cfg`)
                - Updates `csv` data scale (from `lfm`)
                - Creates `lfl` (from `lfm`, `mla` and `csv`)
                - Updates MLA and MAPPED graph data
                - Updates FILTER stage
                - Forces alignment confirmation
        4. FILTER stage - Filter mapped data
            - Invalidate:
                - Resets `lfl` filters
                - Deletes FILTERED graph
                - Invalidates CORRECT stage
            - Update:
                - Applies `lfl` filters (from UI lists)
                - Initializes `lfl.alpha_model` (from `lfl.filtered_locs_2d`)
                - Updates FILTERED graph data
                - Forces update of CORRECT stage
        5. CORRECT stage - Aberration correction
            - Invalidate:
                - Resets `lfl` corrections
                - Deletes CORRECTED graph
                - Invalidates FIT stage
            - Update:
                - Calculates `lfl` correction (from `lfl.filtered_locs_2d`)
                - Initializes `lfl.corrected_locs_2d` (from `lfl.filtered_locs_2d`)
                - Updates CORRECTED graph data
                - Forces update of FIT stage
        6. FIT stage - 3D fitting
            - Invalidate:
                - Deletes `locs_3d`
                - Deletes LOCS_3D, HISTOGRAM and OCCURRENCES graphs
            - Update:
                - Update timestamp
                - Generates `locs_3d` (from `cfg`, `lfm` and `lfl.corrected_locs_2d`)
                - Updates LOCS_3D, HISTOGRAM and OCCURRENCES graphs data
                - Saves results (from `cfg` and `locs_3d`)
    """

    _INVOKE_ON_GUI_EVENT = '<<_InvokeOnGui>>'

    # An entry put on queue from any but GUI thread.
    # The function is invoked from a GUI thread with given arguments.
    class _InvokeOnGuiData:
        def __init__(self, fn, args, kwargs):
            self.fn = fn
            self.args = args
            self.kwargs = kwargs
            self.reply = None
            self.reply_event = threading.Event()

    def __init__(self):
        self.icons = Icons()

        self._root = None
        self._min_root_width: Optional[int] = None
        self._gui_queue: Optional[SimpleQueue] = None

        self.fiji_app = smlfm.FijiApp()

        self.save_timestamp = None

        self.cli_cfg_file: Optional[Path] = None
        self.cli_img_stack: Optional[Path] = None
        self.cli_csv_file: Optional[Path] = None

        self.cfg_file: Optional[Path] = None
        self.cfg: Optional[smlfm.Config] = None

        self.csv: Optional[smlfm.LocalisationFile] = None
        self.lfm: Optional[smlfm.FourierMicroscope] = None
        self.mla: Optional[smlfm.MicroLensArray] = None
        self.lfl: Optional[smlfm.Localisations] = None

        self.locs_3d: Optional[npt.NDArray[float]] = None

        self.graphs: Dict[GraphType, Optional[FigureWindow]] = {}
        for t in GraphType:
            self.graphs[t] = None

        self._ui_mains: Dict[StageType, Optional[ttk.Frame]] = {}
        self._ui_numbers: Dict[StageType, Optional[ttk.Label]] = {}
        self._ui_frames: Dict[StageType, Optional[ttk.Frame]] = {}
        self._stages: Dict[StageType, Optional[IStage]] = {}
        for t in StageType:
            self._ui_numbers[t] = None
            self._ui_frames[t] = None
            self._stages[t] = None

        # Handle CLI options
        for arg in sys.argv[1:]:
            a = arg.casefold()
            if a.endswith('.json'):
                self.cli_cfg_file = Path(arg)
            elif a.endswith('.tiff') or a.endswith('.tif'):
                self.cli_img_stack = Path(arg)
            elif a.endswith('.csv') or a.endswith('.xls'):
                self.cli_csv_file = Path(arg)
            else:
                print(f'WARNING: Ignoring unrecognized option "{arg}"')

    def create_gui(self, root):
        # Import here to avoid circular dependency
        from .config_frame import ConfigFrame  # pylint: disable=import-outside-toplevel
        from .optics_frame import OpticsFrame  # pylint: disable=import-outside-toplevel
        from .csv_frame import CsvFrame  # pylint: disable=import-outside-toplevel
        from .filter_frame import FilterFrame  # pylint: disable=import-outside-toplevel
        from .correct_frame import CorrectFrame  # pylint: disable=import-outside-toplevel
        from .fit_frame import FitFrame  # pylint: disable=import-outside-toplevel

        self._root = root
        self._root.bind(AppModel._INVOKE_ON_GUI_EVENT, self._gui_invoke_handler)
        self._gui_queue = SimpleQueue()

        rows = {
            StageType.CONFIG: (ConfigFrame, self.icons.nr1_large),
            StageType.CSV: (CsvFrame, self.icons.nr2_large),
            StageType.OPTICS: (OpticsFrame, self.icons.nr3_large),
            StageType.FILTER: (FilterFrame, self.icons.nr4_large),
            StageType.CORRECT: (CorrectFrame, self.icons.nr5_large),
            StageType.FIT: (FitFrame, self.icons.nr6_large),
        }
        for i, t in enumerate(StageType):
            self._ui_mains[t] = ttk.Frame(self._root)
            self._ui_numbers[t] = ttk.Label(self._ui_mains[t], image=rows[t][1])
            self._ui_frames[t] = rows[t][0](self._ui_mains[t], self)

            self._ui_numbers[t].grid(column=0, row=0, sticky=tk.NSEW)
            self._ui_frames[t].grid(column=1, row=0, sticky=tk.EW)
            self._ui_mains[t].columnconfigure(index=1, weight=1)
            self._ui_mains[t].grid(sticky=tk.NSEW)

            self._ui_mains[t].configure(padding=0)
            self._ui_numbers[t].configure(padding=(0, 10 if i == 0 else 0, 0, 0))
            self._ui_frames[t].configure(padding=(0, 10 if i == 0 else 0, 10, 10))

            self._stages[t] = self._ui_frames[t]

        self._root.columnconfigure(index=0, weight=1)

        def _update_min_height(_evt=None):
            self._root.update()
            self._root.minsize(self._min_root_width, self._root.bbox()[3])
        for i, t in enumerate(StageType):
            self._ui_frames[t].bind('<Configure>', _update_min_height)

        # Set min. size
        self._root.update()  # Geometry is '1x1+0+0' here, update it first
        self._min_root_width = self._root.winfo_width()
        self._root.minsize(self._min_root_width, self._root.winfo_height())

    def invoke_on_gui_thread_async(self, fn, *args, **kwargs):
        data = AppModel._InvokeOnGuiData(fn, args, kwargs)
        if threading.main_thread().ident == threading.get_ident():
            # Call directly on GUI thread
            data.reply = data.fn(*data.args, *data.kwargs)
        else:
            self._gui_queue.put(data)
            self._root.event_generate(AppModel._INVOKE_ON_GUI_EVENT, when='tail')
            data.reply = None
        return data.reply

    def invoke_on_gui_thread_sync(self, fn, *args, **kwargs):
        data = AppModel._InvokeOnGuiData(fn, args, kwargs)
        if threading.main_thread().ident == threading.get_ident():
            # Call directly on GUI thread
            data.reply = data.fn(*data.args, *data.kwargs)
        else:
            self._gui_queue.put(data)
            self._root.event_generate(AppModel._INVOKE_ON_GUI_EVENT, when='tail')
            data.reply_event.wait()
        return data.reply

    def _gui_invoke_handler(self, _event):
        try:
            while True:
                data = self._gui_queue.get_nowait()
                data.reply = data.fn(*data.args, *data.kwargs)
                data.reply_event.set()
        except Empty:
            pass

    def stage_enabled(self, st: Optional[StageType], enabled: bool):
        if st is not None:
            self._ui_numbers[st].configure(state=tk.NORMAL if enabled else tk.DISABLED)

    def stage_is_active(self, st: Optional[StageType]):
        if st is not None:
            return self._stages[st].stage_is_active()
        return False

    def stage_invalidate(self, st: Optional[StageType]):
        if st is not None:
            self._stages[st].stage_invalidate()

    def stage_start_update(self, st: Optional[StageType]):
        if st is not None:
            self._stages[st].stage_start_update()

    def stage_ui_init(self, st: Optional[StageType]):
        if st is not None:
            self._stages[st].stage_ui_init()

    def stage_ui_flash(self, st: Optional[StageType]):
        if st is not None:
            self._stages[st].stage_ui_flash()

    def stage_ui_updating(self, st: Optional[StageType], updating: bool):
        if st is not None:
            self._stages[st].stage_ui_updating(updating)

    def stages_ui_updating(self, updating: bool):
        for st in StageType:
            self.stage_ui_updating(st, updating)

    def graph_exists(self, gt: GraphType) -> bool:
        return self.graphs[gt] is not None

    def destroy_graph(self, gt: GraphType):
        wnd = self.graphs[gt]
        self.graphs[gt] = None
        if wnd is not None:
            wnd.withdraw()  # Keep that hiding for Unmap binding to work
            wnd.destroy()

    @staticmethod
    def grid_slaves_configure(container: tk.Widget, *args, **kwargs):
        for child in container.grid_slaves():
            child.grid(*args, **kwargs)

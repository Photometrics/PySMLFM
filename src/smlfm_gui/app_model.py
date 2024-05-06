import sys
import threading
import tkinter as tk
from pathlib import Path
from queue import Empty, SimpleQueue
from tkinter import messagebox, ttk
from typing import Dict, Union

import numpy.typing as npt

import smlfm

from .assets import Icons
from .consts import *
from .figure_window import FigureWindow

_has_imagej: bool = True
try:
    import imagej
    import jpype
    import scyjava
except ImportError(imagej):
    _has_imagej = False


class IStage:
    def stage_type(self) -> StageType:
        """Returns the stage type."""
        raise NotImplementedError('Subclass must implement this')

    def stage_type_next(self) -> Union[StageType, None]:
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
        pass

    def stage_ui_updating(self, updating: bool):
        """Changes the stage UI state. If `updating` is True the UI is mostly
        disabled, except some 'Cancel' or 'Abort' button if exists.
        If the update is not in progress, the UI reflects internal state and
        enables UI controls that have valid input data from model."""
        raise NotImplementedError('Subclass must implement this')


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
        self._min_root_width: Union[int, None] = None
        self._gui_queue: Union[SimpleQueue, None] = None

        # One time detection during app start if PyImageJ package is installed
        self.has_imagej: bool = _has_imagej
        # Detected during update of CFG stage
        # Once detected, it cannot be deactivated as Java can only be started once
        self.has_fiji: bool = False
        # A path where Fiji app has been detected
        # Modified value will apply only after app restarts
        self.fiji_dir: Union[Path, None] = None
        # A list with options for JVM
        # Modified value will apply only after app restarts
        self.fiji_jvm_opts: str = ''
        # ImageJ/Fiji instance, if detected
        if _has_imagej:
            self.ij: Union[jpype.JClass, None] = None

        self.save_timestamp = None

        self.cli_cfg_file: Union[Path, None] = None
        self.cli_csv_file: Union[Path, None] = None

        self.cfg_file: Union[Path, None] = None
        self.cfg: Union[smlfm.Config, None] = None

        self.csv: Union[smlfm.LocalisationFile, None] = None
        self.lfm: Union[smlfm.FourierMicroscope, None] = None
        self.mla: Union[smlfm.MicroLensArray, None] = None
        self.lfl: Union[smlfm.Localisations, None] = None

        self.locs_3d: Union[npt.NDArray[float], None] = None

        self.graphs: Dict[GraphType, Union[FigureWindow, None]] = dict()
        for t in GraphType:
            self.graphs[t] = None

        self._ui_mains: Dict[StageType, Union[ttk.Frame, None]] = dict()
        self._ui_numbers: Dict[StageType, Union[ttk.Label, None]] = dict()
        self._ui_frames: Dict[StageType, Union[ttk.Frame, None]] = dict()
        self._stages: Dict[StageType, Union[IStage, None]] = dict()
        for t in StageType:
            self._ui_numbers[t] = None
            self._ui_frames[t] = None
            self._stages[t] = None

        # Handle CLI options
        for arg in sys.argv[1:]:
            a = arg.casefold()
            if a.endswith('.json'):
                self.cli_cfg_file = Path(arg)
            elif a.endswith('.csv') or a.endswith('.xls'):
                self.cli_csv_file = Path(arg)
            else:
                print(f'WARNING: Ignoring unrecognized option "{arg}"')

    def create_gui(self, root):
        # Import here to avoid circular dependency
        from .config_frame import ConfigFrame
        from .optics_frame import OpticsFrame
        from .csv_frame import CsvFrame
        from .filter_frame import FilterFrame
        from .correct_frame import CorrectFrame
        from .fit_frame import FitFrame

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

    def stage_enabled(self, st: Union[StageType, None], enabled: bool):
        if st is not None:
            self._ui_numbers[st].configure(state=tk.NORMAL if enabled else tk.DISABLED)

    def stage_is_active(self, st: Union[StageType, None]):
        if st is not None:
            return self._stages[st].stage_is_active()
        return False

    def stage_invalidate(self, st: Union[StageType, None]):
        if st is not None:
            self._stages[st].stage_invalidate()

    def stage_start_update(self, st: Union[StageType, None]):
        if st is not None:
            self._stages[st].stage_start_update()

    def stage_ui_init(self, st: Union[StageType, None]):
        if st is not None:
            self._stages[st].stage_ui_init()

    def stage_ui_flash(self, st: Union[StageType, None]):
        if st is not None:
            self._stages[st].stage_ui_flash()

    def stage_ui_updating(self, st: Union[StageType, None], updating: bool):
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

    # Can be executed on thread
    def detect_fiji(self):
        fiji_dir = self.cfg.fiji_dir
        fiji_jvm_opts = self.cfg.fiji_jvm_opts
        if self.has_fiji:
            # Once detected, it cannot be deactivated as Java can only be started once
            if fiji_dir != self.fiji_dir or fiji_jvm_opts != self.fiji_jvm_opts:
                print('WARNING: Restart the application to apply new settings')
                self.invoke_on_gui_thread_async(
                    messagebox.showwarning,
                    kwargs=dict(
                        title='Warning',
                        message='Restart the application to apply new settings.',
                        detail='Java can be started only once.'))
            return
        if not self.has_imagej:
            # PyImageJ not installed
            return
        if fiji_dir is None:
            return

        try:
            jvm_opts = fiji_jvm_opts.split()
            scyjava.config.add_options(jvm_opts)
            self.ij = imagej.init(str(fiji_dir), mode=imagej.Mode.INTERACTIVE)
        except RuntimeError:
            return

        print(f'ImageJ version(s): {self.ij.getVersion()}')
        print(f'IJ app version: {self.ij.app().getVersion()}')

        self.has_fiji = True
        self.fiji_dir = fiji_dir
        self.fiji_jvm_opts = fiji_jvm_opts

    # Can be executed on thread
    def run_peakfit(self):
        j_stack = self.ij.io().open(str(self.cfg.img_stack))
        j_imp_stack = self.ij.py.to_imageplus(j_stack)

        res_dir = self.cfg.csv_file.parent

        # noinspection PyPep8Naming
        HOME = Path.home()

        # Settings for a PeakFit ImageJ plugin
        peakfit_args = {
            'template': '',
        }
        if not (HOME / '.gdsc.smlm' / 'calibration.settings').exists():
            peakfit_args.update({
                'camera_type': 'EMCCD',
                'camera_bias': 400.00,
                'gain': 40.0000,
                'read_noise': 7.1600,
                'calibration': 266.0,
                'exposure_time': 30.0,
            })
        if not (HOME / '.gdsc.smlm' / 'psf.settings').exists():
            peakfit_args.update({
                'psf': 'Circular Gaussian 2D',
                'psf_parameter_1': 1.700,
            })
        if True:
            peakfit_args.update({
                'spot_filter_type': 'Difference',
                'spot_filter2': 'Mean',
                'smoothing2': 2.0,
            })
        if not (HOME / '.gdsc.smlm' / 'fitenginesettings.settings').exists():
            peakfit_args.update({
                # 'spot_filter_type': 'Difference',
                # 'spot_filter2': 'Mean',
                # 'smoothing2': 2.0,
                'spot_filter': 'Mean',
                'smoothing': 0.32,
                'search_width': 0.90,
                'border_width': 4.00,
                'fitting_width': 4.00,

                'fit_solver': 'LVM LSE',
                'relative_threshold': 1.0E-6,
                'absolute_threshold': 1.0E-16,
                'parameter_relative_threshold': 0.0,
                'parameter_absolute_threshold': 0.0,
                'max_iterations': 20,
                'lambda': 10.0000,
                'fail_limit': 3,
                'pass_rate': 0.50,

                'neighbour_height': 0.30,
                'residuals_threshold': 1.00,
                'duplicate_distance': 0.50,
                'duplicate_distance_absolute': True,

                'shift_factor': 1.2,
                'signal_strength': 3.0,
                'min_photons': 10.0,
                'min_width_factor': 0.4,
                'max_width_factor': 1.0,
                'precision': 75.0,
                'precision_method': 'Mortensen',
            })
        # Overwrite result settings unconditionally
        # if not (HOME / '.gdsc.smlm' / 'resultssettings.settings').exists():
        if True:
            peakfit_args.update({
                'results_format': 'Text',
                'file_distance_unit': 'unknown (na)',
                'file_intensity_unit': 'unknown (na)',
                'file_angle_unit': 'unknown (na)',
                'file_show_precision': True,
                'results_directory': str(res_dir),
            })
        # Temporary settings for development
        peakfit_args.update({
            # 'log_progress': True,

            'image': 'None',
            # 'image': 'Localisations (width=precision)',
            'equalised': True,
            'image_size_mode': 'Scaled',
            'image_scale': 1,
            'lut': 'Fire',
        })

        was_log_window_open = self.ij.WindowManager.getWindow("Log") is not None

        # Apply our configuration
        self.ij.py.run_plugin('Fit Configuration', args=peakfit_args)
        # Allow user to change the configuration
        self.ij.py.run_plugin('Fit Configuration')
        # Run the plugin code on given stack
        self.ij.py.run_plugin('Peak Fit', args=peakfit_args, imp=j_imp_stack)

        # Close Log window if it wasn't open before Peak Fit
        if not was_log_window_open:
            log_window = self.ij.WindowManager.getWindow("Log")
            if log_window is not None:
                log_window.setVisible(False)

        res_xls_file = res_dir / (self.cfg.img_stack.name + '.results.xls')
        # Rename to configured CSV file (overwrite if exists)
        res_xls_file.replace(self.cfg.csv_file)

    @staticmethod
    def grid_slaves_configure(container: tk.Widget, *args, **kwargs):
        for child in container.grid_slaves():
            child.grid(*args, **kwargs)

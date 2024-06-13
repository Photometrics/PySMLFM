import json
from dataclasses import asdict, dataclass, field, fields, is_dataclass
from enum import Enum
from pathlib import Path, PurePath
from typing import Optional, Tuple

from .fitting import Fitting
from .localisation_file import LocalisationFile
from .localisations import Localisations
from .micro_lens_array import MicroLensArray


@dataclass
# pylint: disable=too-many-instance-attributes
class Config:
    _fiji_dir_doc: str = (
        'A path to Fiji.app folder with Fiji application.\n'
        'Fiji is needed to find localizations in an image stack via PeakFit plugin.\n'
        'If set to \'null\' or empty string, a CSV file must be given.')
    fiji_dir: Optional[Path] = None
    _fiji_jvm_opts_doc: str = (
        'A list of space separated options for Java Virtual Machine started by Fiji.')
    fiji_jvm_opts: str = '-Xmx10g'
    _img_stack_doc: str = (
        'A path to image stack file to be analyzed by PeakFit plugin in Fiji.\n'
        'If the Fiji application is not detected, this value is ignored.\n'
        'Otherwise, the output from PeakFit plugin is stored in configured CSV file.')
    img_stack: Optional[Path] = None
    _csv_file_doc: str = (
        'A path to CSV/XLS file with localisations.\n'
        'If the image stack file is given and if Fiji application is found,\n'
        'this file is overwritten with PeakFit output.')
    csv_file: Optional[Path] = None
    _csv_format_doc: str = (
        'A format of CSV file with localisations.\n'
        'Supported values: \'PEAKFIT\', \'THUNDERSTORM\', \'PICASSO\'.')
    csv_format: LocalisationFile.Format = LocalisationFile.Format.PEAKFIT

    _mla_type_doc: str = (
        'A Micro-Lens Array lens arrangement.\n'
        'Supported values: \'HEXAGONAL\', \'SQUARE\'.')
    mla_type: MicroLensArray.LatticeType = MicroLensArray.LatticeType.HEXAGONAL
    _mla_lens_pitch_doc: str = (
        'A pitch along X direction (in microns).')
    mla_lens_pitch: float = 2390.0
    _mla_optic_size_doc: str = (
        'A size of MLA optic (in microns).')
    mla_optic_size: float = 10000.0
    _mla_centre_doc: str = (
        'An X,Y coordinates of the array center (in lattice spacing units).\n'
        'The MLA keeps the distance between lens centres equal to 1.')
    mla_centre: Tuple[float, float] = field(default_factory=lambda: (0.0, 0.0))
    _mla_rotation_doc: str = (
        'A rotation of the MLA to match the orientation of the data (in degrees)')
    mla_rotation: float = 30.8
    _mla_offset_doc: str = (
        'An X,Y offset of the MLA to match the orientation of the data (in microns).')
    mla_offset: Tuple[float, float] = field(default_factory=lambda: (0.0, 0.0))
    _focal_length_mla_doc: str = (
        'A focal length of Micro-Lens Array (in mm).')
    focal_length_mla: float = 175.0

    _focal_length_obj_lens_doc: str = (
        'A focal length of the objective lens (in mm).')
    focal_length_obj_lens: float = 200.0 / 60.0
    _focal_length_fourier_lens_doc: str = (
        'A focal length of the fourier lens (in mm).')
    focal_length_fourier_lens: float = 175.0
    _focal_length_tube_lens_doc: str = (
        'A focal length of the tube lens (in mm).')
    focal_length_tube_lens: float = 200.0

    _num_aperture_doc: str = (
        'A numerical aperture of the objective.')
    num_aperture: float = 1.27
    _ref_idx_immersion_doc: str = (
        'An immersion refractive index.')
    ref_idx_immersion: float = 1.33
    _ref_idx_medium_doc: str = (
        'A specimen/medium refractive index.')
    ref_idx_medium: float = 1.33

    _pixel_size_camera_doc: str = (
        'A camera pixel size (in microns).')
    pixel_size_camera: float = 16.0

    _filter_lenses_doc: str = (
        'Filter out all localizations mapped to the lenses with center\n'
        'lying outside the back focal plane.')
    filter_lenses: bool = True
    _filter_rhos_doc: str = (
        'Filter out all localizations with distance to origin\n'
        'lying outside given min,max range (in normalised pupil coordinates).')
    filter_rhos: Optional[Tuple[float, float]] = None
    _filter_spot_sizes_doc: str = (
        'Filter out all localizations with spot size\n'
        'lying outside given min,max range (in microns).')
    filter_spot_sizes: Optional[Tuple[float, float]] = None
    _filter_photons_doc: str = (
        'Filter out all localizations with background intensity\n'
        'lying outside given min,max range (in photons).')
    filter_photons: Optional[Tuple[float, float]] = None
    _alpha_model_doc: str = (
        'A model used for mapping.\n'
        'Supported values: \'LINEAR\', \'SPHERE\', \'INTEGRATE_SPHERE\'.')
    alpha_model: Localisations.AlphaModel = Localisations.AlphaModel.INTEGRATE_SPHERE

    _fit_params_aberration_doc: str = (
        'A fitting parameters for aberration correction purposes.')
    _fit_params_aberration_frame_min_doc: str = (
        'A min. frame number, zero or negative to auto-fill min. value.')
    _fit_params_aberration_frame_max_doc: str = (
        'A max. frame number, zero or negative to auto-fill default value 1000.')
    _fit_params_aberration_disparity_max_doc: str = (
        'A limit of possible disparity between adjacent views,\n'
        'from negative to positive value (in microns).')
    _fit_params_aberration_disparity_step_doc: str = (
        'A step used for disparity range (in microns).')
    _fit_params_aberration_dist_search_doc: str = (
        'A window to accept points as belonging to a given Z (in microns).')
    _fit_params_aberration_angle_tolerance_doc: str = (
        'A tolerance for selecting with angles around relative U,V (in degrees).')
    _fit_params_aberration_threshold_doc: str = (
        'A max. distance of the candidate (in microns).')
    _fit_params_aberration_min_views_doc: str = (
        'A min. number of views the candidate is seen to count it.')
    _fit_params_aberration_z_calib_doc: str = (
        'A calibration factor between optical and physical Z axis.\n'
        'Unused and ignored for aberration correction.')
    fit_params_aberration: Fitting.FitParams = field(
        default_factory=lambda: Fitting.FitParams(
            frame_min=-1,
            frame_max=-1,
            disparity_max=5.0,
            disparity_step=0.1,
            dist_search=0.5,
            angle_tolerance=2.0,
            threshold=1.0,
            min_views=3,
            z_calib=None,
        )
    )
    _aberration_params_doc: str = (
        'Parameters for aberration correction.')
    _aberration_params_axial_window_doc: str = (
        'A max. standard error in Z to apply correction (in microns).')
    _aberration_params_photon_threshold_doc: str = (
        'A min. number of photons to apply correction.')
    _aberration_params_min_views_doc: str = (
        'A min. number of views the candidate is seen to count it.')
    aberration_params: Fitting.AberrationParams = field(
        default_factory=lambda: Fitting.AberrationParams(
            axial_window=1.0,
            photon_threshold=1,
            min_views=3,
        )
    )
    _fit_params_full_doc: str = (
        'A fitting parameters for full data set, used after aberration correction.')
    _fit_params_full_frame_min_doc: str = (
        'A min. frame number, zero or negative to auto-fill min. value.')
    _fit_params_full_frame_max_doc: str = (
        'A max. frame number, zero or negative to auto-fill max. value.')
    _fit_params_full_disparity_max_doc: str = (
        'A limit of possible disparity between adjacent views,\n'
        'from negative to positive value (in microns).')
    _fit_params_full_disparity_step_doc: str = (
        'A step used for disparity range (in microns).')
    _fit_params_full_dist_search_doc: str = (
        'A window to accept points as belonging to a given Z (in microns).')
    _fit_params_full_angle_tolerance_doc: str = (
        'A tolerance for selecting with angles around relative U,V (in degrees).')
    _fit_params_full_threshold_doc: str = (
        'A max. distance of the candidate (in microns).')
    _fit_params_full_min_views_doc: str = (
        'A min. number of views the candidate is seen to count it.')
    _fit_params_full_z_calib_doc: str = (
        'A calibration factor between optical and physical Z axis.')
    fit_params_full: Fitting.FitParams = field(
        default_factory=lambda: Fitting.FitParams(
            frame_min=-1,
            frame_max=-1,
            disparity_max=8.0,
            disparity_step=0.1,
            dist_search=0.5,
            angle_tolerance=1.0,
            threshold=0.3,
            min_views=2,
            z_calib=1.53,
        )
    )

    _save_dir_doc: str = (
        'Save the results to a new sub-folder under this directory.\n'
        'If set to \'null\' or empty string, nothing is saved.\n'
        'Defaults to current working directory.')
    save_dir: Optional[Path] = Path()

    _show_graphs_doc: str = (
        'Show various graphs, a global switch.\n'
        'In CLI app it pops up GUI windows, so e.g. on Linux an X server\n'
        'or Wayland must be running and DISPLAY env. var. must be set.')
    show_graphs: bool = True
    _show_result_graphs_doc: str = (
        'Show only final three graphs with 3D view, histogram and errors.')
    show_result_graphs: bool = True
    _show_mla_alignment_graph_doc: str = (
        'Show micro-lenses together with localisations.')
    show_mla_alignment_graph: bool = True
    _show_all_debug_graphs_doc: str = (
        'Show all remaining graphs.')
    show_all_debug_graphs: bool = False

    _show_max_lateral_err_doc: str = (
        'In result graphs show only points with lateral error below this value.')
    show_max_lateral_err: Optional[float] = None
    _show_min_view_count_doc: str = (
        'In result graphs show only points with view count below this value.')
    show_min_view_count: Optional[int] = None

    _confirm_mla_alignment_doc: str = (
        'Ask the user to confirm the data and MLA alignment.\n'
        'This is only active with \'show_mla_alignment_graph\'.')
    confirm_mla_alignment: bool = True

    _log_timing_doc: str = (
        'Print timing messages to console for all lengthy operations.')
    log_timing: bool = True

    _max_workers_doc: str = (
        'Limit the number of parallel workers used to speed up some computations.\n'
        'If set to zero or less all CPUs in the system are used.')
    max_workers: int = 0

    def to_json(self, **kwargs):
        indent = kwargs.pop('indent', 4)  # Indent with 4 spaces by default

        class JSONEncoder(json.JSONEncoder):
            def default(self, o):
                if is_dataclass(o):
                    return asdict(o)
                if isinstance(o, PurePath):
                    return str(o)
                if isinstance(o, Enum):
                    return o.name
                return super().default(o)

        return json.dumps(self, cls=JSONEncoder,
                          indent=indent, ensure_ascii=False,
                          **kwargs)

    @staticmethod
    def from_json(dump: str):
        cfg = Config(**json.loads(dump))
        cfg_default = Config()

        for f in fields(Config):
            # Override doc fields with internal documentation
            if f.name.startswith('_') and f.name.endswith('_doc'):
                setattr(cfg, f.name, getattr(cfg_default, f.name))
                continue

            value = getattr(cfg, f.name)
            if repr(f.type) == repr(Optional[Path]):
                if value is not None:
                    setattr(cfg, f.name, Path(value))
            elif repr(f.type) == repr(Tuple[float, float]):
                setattr(cfg, f.name, tuple(value))
            elif repr(f.type) == repr(Optional[Tuple[float, float]]):
                if value is not None:
                    setattr(cfg, f.name, tuple(value))
            elif f.type is LocalisationFile.Format:
                setattr(cfg, f.name, LocalisationFile.Format[value])
            elif f.type is Localisations.AlphaModel:
                setattr(cfg, f.name, Localisations.AlphaModel[value])
            elif f.type is MicroLensArray.LatticeType:
                setattr(cfg, f.name, MicroLensArray.LatticeType[value])
            elif f.type is Fitting.FitParams:
                setattr(cfg, f.name, Fitting.FitParams(**value))
            elif f.type is Fitting.AberrationParams:
                setattr(cfg, f.name, Fitting.AberrationParams(**value))

        return cfg

import dataclasses
import json
from dataclasses import dataclass, fields
from enum import Enum
from pathlib import Path, PurePath
from typing import Optional, Tuple

import numpy as np
import numpy.typing as npt

from .fitting import Fitting
from .localisation_file import LocalisationFile
from .localisations import Localisations
from .micro_lens_array import MicroLensArray


@dataclass
class Config:
    _csv_file_doc: str = (
        'A path to CSV file with localisations.\n'
        'A CLI application requires this to be a valid path to existing file.\n'
        'A GUI application can call PeakFit plugin from Fiji and use this\n'
        'path to say Fiji where to store the PeakFit output.\n'
        'The \'null\' value is allowed only when loading from JSON to allow\n'
        'the application ask user interactively.')
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
    mla_centre: npt.NDArray[float] = np.array([0.0, 0.0])
    _mla_rotation_doc: str = (
        'A rotation of the MLA to match the orientation of the data (in degrees)')
    mla_rotation: float = 30.8
    _mla_offset_doc: str = (
        'An X,Y offset of the MLA to match the orientation of the data (in microns).')
    mla_offset: npt.NDArray[float] = np.array([0.0, 0.0])
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
        'A calibration factor between optical and physical Z axis.')
    fit_params_aberration: Fitting.FitParams = Fitting.FitParams(
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
    _aberration_params_doc: str = (
        'Parameters for aberration correction.')
    _aberration_params_axial_window_doc: str = (
        'A max. standard error in Z to apply correction (in microns).')
    _aberration_params_photon_threshold_doc: str = (
        'A min. number of photons to apply correction.')
    _aberration_params_min_views_doc: str = (
        'A min. number of views the candidate is seen to count it.')
    aberration_params: Fitting.AberrationParams = Fitting.AberrationParams(
        axial_window=1,
        photon_threshold=1,
        min_views=3,
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
    fit_params_full: Fitting.FitParams = Fitting.FitParams(
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
            def default(self, obj):
                if dataclasses.is_dataclass(obj):
                    return dataclasses.asdict(obj)
                elif isinstance(obj, PurePath):
                    return str(obj)
                elif isinstance(obj, Enum):
                    return obj.name
                elif isinstance(obj, np.ndarray):
                    return obj.tolist()
                return super().default(obj)

        return json.dumps(self, cls=JSONEncoder,
                          indent=indent, ensure_ascii=False,
                          **kwargs)

    @staticmethod
    def from_json(dump: str):
        cfg = Config(**json.loads(dump))
        cfg_default = Config()

        for field in fields(Config):
            # Override doc fields with internal documentation
            if field.name.startswith('_') and field.name.endswith('_doc'):
                cfg.__setattr__(field.name, getattr(cfg_default, field.name))
                continue

            value = getattr(cfg, field.name)
            if field.type is Path and value is not None:
                cfg.__setattr__(field.name, Path(value))
            elif field.type is Optional[Path] and value is not None:
                cfg.__setattr__(field.name, Path(value))
            elif field.type is LocalisationFile.Format:
                cfg.__setattr__(field.name, LocalisationFile.Format[value])
            elif field.type is Localisations.AlphaModel:
                cfg.__setattr__(field.name, Localisations.AlphaModel[value])
            elif field.type is MicroLensArray.LatticeType:
                cfg.__setattr__(field.name, MicroLensArray.LatticeType[value])
            elif (False  # field.type is np.ndarray  # NDArray is deserialized to list
                  or field.name == 'mla_centre'
                  or field.name == 'mla_offset'):
                cfg.__setattr__(field.name, np.array(value))
            elif field.type is Fitting.FitParams:
                cfg.__setattr__(field.name, Fitting.FitParams(**value))
            elif field.type is Fitting.AberrationParams:
                cfg.__setattr__(field.name, Fitting.AberrationParams(**value))

        return cfg

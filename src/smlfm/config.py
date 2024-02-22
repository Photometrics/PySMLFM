import dataclasses
import json
from dataclasses import dataclass, fields
from enum import Enum
from pathlib import Path, PurePath
from typing import Union

import numpy as np
import numpy.typing as npt

from .fitting import Fitting
from .localisation_file import LocalisationFile
from .micro_lens_array import MicroLensArray


@dataclass
class Config:
    # A path to CSV file with localisations.
    # A CLI app requires this to be a valid path to existing file.
    # A GUI app can call PeakFit plugin from ImageJ and use this path where
    # ImageJ stores the PeakFit output.
    # The 'None' value is allowed only when loading from JSON to allow the
    # application ask user interactively.
    csv_file: Union[Path, None]

    # A CSV file format with localisations
    csv_format: LocalisationFile.Format

    # An MLA lens arrangement
    mla_type: MicroLensArray.LatticeType
    # A pitch along X direction (in microns)
    mla_lens_pitch: float
    # A size of MLA optic (in microns)
    mla_optic_size: float
    # An X,Y coordinates of the array center (lattice spacing units).
    # MLA keeps the distance between lens centres equal to 1.
    mla_centre: npt.NDArray[float]
    # A rotation of the MLA to match the orientation of the data (in degrees)
    mla_rotation: float
    # An offset of the MLA to match the orientation of the data (in microns)
    mla_offset: npt.NDArray[float]
    # A focal length of micro-lens array (in mm)
    focal_length_mla: float

    # A focal length of the objective lens (in mm)
    focal_length_obj_lens: float
    # A focal length of the fourier lens (in mm)
    focal_length_fourier_lens: float
    # A focal length of the tube lens (in mm)
    focal_length_tube_lens: float

    # A numerical aperture of the objective
    num_aperture: float
    # An immersion refractive index
    ref_idx_immersion: float
    # A specimen/medium refractive index
    ref_idx_medium: float

    # A camera pixel size (in microns)
    pixel_size_camera: float

    # Fitting parameters for aberration purposes.
    fit_params_aberration: Fitting.FitParams
    # Parameters for aberration correction.
    aberration_params: Fitting.AberrationParams
    # Fitting parameters for full data set, used after aberration.
    fit_params_full: Fitting.FitParams

    # Save the results to a new sub-folder in this directory.
    # If set to `None` nothing is saved. Defaults to current working directory.
    save_dir: Union[Path, None] = Path()

    # Show various graphs. In CLI app it pops up GUI windows, so e.g.
    # on Linux an X server or Wayland must be running and DISPLAY env. var.
    # must be set.
    show_graphs: bool = False
    # Show only final three graphs with 3D view, histogram and errors.
    show_result_graphs: bool = True
    # Show micro-lenses and input data. The app can ask user to confirm
    # the alignment before continue, see `confirm_mla_alignment`.
    show_mla_alignment_graph: bool = True
    # Show all remaining graphs.
    show_all_debug_graphs: bool = False

    # In result graphs show only points with lateral error below this value.
    show_max_lateral_err: Union[float, None] = None
    # In result graphs show only points with lateral error below this value.
    show_min_view_count: Union[int, None] = None

    # Ask the user to confirm the data and MLA alignment.
    # This is only active with `show_mla_alignment_graph`.
    confirm_mla_alignment: bool = True

    # Print timing messages for all lengthy operations.
    log_timing: bool = True

    def to_json(self, **kwargs):
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

        return json.dumps(self, cls=JSONEncoder, **kwargs)

    @staticmethod
    def from_json(dump: str):
        cfg = Config(**json.loads(dump))

        for field in fields(Config):
            value = getattr(cfg, field.name)
            if field.type is Path and value is not None:
                cfg.__setattr__(field.name, Path(value))
            elif field.type is Union[Path, None] and value is not None:
                cfg.__setattr__(field.name, Path(value))
            elif field.type is LocalisationFile.Format:
                cfg.__setattr__(field.name, LocalisationFile.Format[value])
            elif field.type is MicroLensArray.LatticeType:
                cfg.__setattr__(field.name, MicroLensArray.LatticeType[value])
            elif (field.type is np.ndarray  # NDArray is deserialized to list
                  or field.name == 'mla_centre'
                  or field.name == 'mla_offset'):
                cfg.__setattr__(field.name, np.array(value))
            elif field.type is Fitting.FitParams:
                cfg.__setattr__(field.name, Fitting.FitParams(**value))
            elif field.type is Fitting.AberrationParams:
                cfg.__setattr__(field.name, Fitting.AberrationParams(**value))

        return cfg

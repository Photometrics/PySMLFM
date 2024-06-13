import tkinter as tk
from idlelib.tooltip import Hovertip
from tkinter import ttk
from typing import Callable, Optional

import smlfm
from .app_model import AppModel
from .cfg_dialog import CfgDialog
from .consts import READONLY


# pylint: disable=too-many-instance-attributes
class OpticsCfgDialog(CfgDialog):

    def __init__(self, parent, model: AppModel, title: Optional[str] = None,
                 process_cb: Optional[Callable[[bool], None]] = None):
        if title is None:
            title = 'Optics Settings'

        self._ui_mla_type: Optional[ttk.Combobox] = None
        self._var_mla_type = tk.StringVar(value=model.cfg.mla_type.name)

        self._ui_mla_lens_pitch: Optional[ttk.Entry] = None
        self._var_mla_lens_pitch = tk.StringVar(value=str(model.cfg.mla_lens_pitch))
        self._ui_mla_lens_pitch_tip: Optional[Hovertip] = None

        self._ui_mla_optic_size: Optional[ttk.Entry] = None
        self._var_mla_optic_size = tk.StringVar(value=str(model.cfg.mla_optic_size))
        self._ui_mla_optic_size_tip: Optional[Hovertip] = None

        self._ui_mla_centre_x: Optional[ttk.Entry] = None
        self._var_mla_centre_x = tk.StringVar(value=str(model.cfg.mla_centre[0]))
        self._ui_mla_centre_x_tip: Optional[Hovertip] = None
        self._ui_mla_centre_y: Optional[ttk.Entry] = None
        self._var_mla_centre_y = tk.StringVar(value=str(model.cfg.mla_centre[1]))
        self._ui_mla_centre_y_tip: Optional[Hovertip] = None

        self._ui_mla_rotation: Optional[ttk.Entry] = None
        self._var_mla_rotation = tk.StringVar(value=str(model.cfg.mla_rotation))
        self._ui_mla_rotation_tip: Optional[Hovertip] = None

        self._ui_mla_offset_x: Optional[ttk.Entry] = None
        self._var_mla_offset_x = tk.StringVar(value=str(model.cfg.mla_offset[0]))
        self._ui_mla_offset_x_tip: Optional[Hovertip] = None
        self._ui_mla_offset_y: Optional[ttk.Entry] = None
        self._var_mla_offset_y = tk.StringVar(value=str(model.cfg.mla_offset[1]))
        self._ui_mla_offset_y_tip: Optional[Hovertip] = None

        self._ui_focal_length_mla: Optional[ttk.Entry] = None
        self._var_focal_length_mla = tk.StringVar(
            value=str(model.cfg.focal_length_mla))
        self._ui_focal_length_mla_tip: Optional[Hovertip] = None

        self._ui_focal_length_obj_lens: Optional[ttk.Entry] = None
        self._var_focal_length_obj_lens = tk.StringVar(
            value=str(model.cfg.focal_length_obj_lens))
        self._ui_focal_length_obj_lens_tip: Optional[Hovertip] = None

        self._ui_focal_length_fourier_lens: Optional[ttk.Entry] = None
        self._var_focal_length_fourier_lens = tk.StringVar(
            value=str(model.cfg.focal_length_fourier_lens))
        self._ui_focal_length_fourier_lens_tip: Optional[Hovertip] = None

        self._ui_focal_length_tube_lens: Optional[ttk.Entry] = None
        self._var_focal_length_tube_lens = tk.StringVar(
            value=str(model.cfg.focal_length_tube_lens))
        self._ui_focal_length_tube_lens_tip: Optional[Hovertip] = None

        self._ui_num_aperture: Optional[ttk.Entry] = None
        self._var_num_aperture = tk.StringVar(value=str(model.cfg.num_aperture))
        self._ui_num_aperture_tip: Optional[Hovertip] = None

        self._ui_ref_idx_immersion: Optional[ttk.Entry] = None
        self._var_ref_idx_immersion = tk.StringVar(
            value=str(model.cfg.ref_idx_immersion))
        self._ui_ref_idx_immersion_tip: Optional[Hovertip] = None

        self._ui_ref_idx_medium: Optional[ttk.Entry] = None
        self._var_ref_idx_medium = tk.StringVar(value=str(model.cfg.ref_idx_medium))
        self._ui_ref_idx_medium_tip: Optional[Hovertip] = None

        self._ui_pixel_size_camera: Optional[ttk.Entry] = None
        self._var_pixel_size_camera = tk.StringVar(
            value=str(model.cfg.pixel_size_camera))
        self._ui_pixel_size_camera_tip: Optional[Hovertip] = None

        super().__init__(parent, model, title, process_cb=process_cb)

    # noinspection PyProtectedMember
    # pylint: disable=protected-access,too-many-statements
    def body(self, master) -> tk.BaseWidget:
        ui_tab = ttk.Frame(master)
        row = 0

        ui_mla_type_lbl = ttk.Label(ui_tab, text='MLA lattice type:', anchor=tk.E)
        Hovertip(ui_mla_type_lbl, text=self.model.cfg._mla_type_doc)
        self._ui_mla_type = ttk.Combobox(
            ui_tab, state=READONLY,
            values=[t.name for t in smlfm.MicroLensArray.LatticeType],
            textvariable=self._var_mla_type)
        Hovertip(self._ui_mla_type, text=self.model.cfg._mla_type_doc)
        self.ui_widgets.append(self._ui_mla_type)
        #
        ui_mla_type_lbl.grid(column=0, row=row, sticky=tk.W)
        self._ui_mla_type.grid(column=1, row=row, sticky=tk.EW, columnspan=2)
        row += 1

        ui_mla_lens_pitch_lbl = ttk.Label(ui_tab, text='MLA lens pitch:', anchor=tk.E)
        Hovertip(ui_mla_lens_pitch_lbl, text=self.model.cfg._mla_lens_pitch_doc)
        self._ui_mla_lens_pitch = ttk.Entry(
            ui_tab, textvariable=self._var_mla_lens_pitch)
        self._ui_mla_lens_pitch_tip = Hovertip(
            self._ui_mla_lens_pitch, text=self.model.cfg._mla_lens_pitch_doc)
        self.ui_widgets.append(self._ui_mla_lens_pitch)
        ui_mla_lens_pitch_unit = ttk.Label(ui_tab, text='\u00B5m')  # microns
        #
        ui_mla_lens_pitch_lbl.grid(column=0, row=row, sticky=tk.W)
        self._ui_mla_lens_pitch.grid(column=1, row=row, sticky=tk.EW, columnspan=2)
        ui_mla_lens_pitch_unit.grid(column=3, row=row, sticky=tk.W)
        row += 1

        ui_mla_optic_size_lbl = ttk.Label(ui_tab, text='MLA optic size:', anchor=tk.E)
        Hovertip(ui_mla_optic_size_lbl, text=self.model.cfg._mla_optic_size_doc)
        self._ui_mla_optic_size = ttk.Entry(
            ui_tab, textvariable=self._var_mla_optic_size)
        self._ui_mla_optic_size_tip = Hovertip(
            self._ui_mla_optic_size, text=self.model.cfg._mla_optic_size_doc)
        self.ui_widgets.append(self._ui_mla_optic_size)
        ui_mla_optic_size_unit = ttk.Label(ui_tab, text='\u00B5m')  # microns
        #
        ui_mla_optic_size_lbl.grid(column=0, row=row, sticky=tk.W)
        self._ui_mla_optic_size.grid(column=1, row=row, sticky=tk.EW, columnspan=2)
        ui_mla_optic_size_unit.grid(column=3, row=row, sticky=tk.W)
        row += 1

        ui_mla_centre_lbl = ttk.Label(ui_tab, text='MLA centre:', anchor=tk.E)
        Hovertip(ui_mla_centre_lbl, text=self.model.cfg._mla_centre_doc)
        self._ui_mla_centre_x = ttk.Entry(
            ui_tab, textvariable=self._var_mla_centre_x)
        self._ui_mla_centre_x_tip = Hovertip(
            self._ui_mla_centre_x, text=self.model.cfg._mla_centre_doc)
        self.ui_widgets.append(self._ui_mla_centre_x)
        self._ui_mla_centre_y = ttk.Entry(
            ui_tab, textvariable=self._var_mla_centre_y)
        self._ui_mla_centre_y_tip = Hovertip(
            self._ui_mla_centre_y, text=self.model.cfg._mla_centre_doc)
        self.ui_widgets.append(self._ui_mla_centre_y)
        ui_mla_centre_unit = ttk.Label(ui_tab, text='[lsu]')
        Hovertip(ui_mla_centre_unit, text='lattice spacing units')
        #
        ui_mla_centre_lbl.grid(column=0, row=row, sticky=tk.W)
        self._ui_mla_centre_x.grid(column=1, row=row, sticky=tk.EW)
        self._ui_mla_centre_y.grid(column=2, row=row, sticky=tk.EW)
        ui_mla_centre_unit.grid(column=3, row=row, sticky=tk.W)
        row += 1

        ui_mla_rotation_lbl = ttk.Label(ui_tab, text='MLA rotation:', anchor=tk.E)
        Hovertip(ui_mla_rotation_lbl, text=self.model.cfg._mla_rotation_doc)
        self._ui_mla_rotation = ttk.Entry(
            ui_tab, textvariable=self._var_mla_rotation)
        self._ui_mla_rotation_tip = Hovertip(
            self._ui_mla_rotation, text=self.model.cfg._mla_rotation_doc)
        self.ui_widgets.append(self._ui_mla_rotation)
        ui_mla_rotation_unit = ttk.Label(ui_tab, text='deg')
        #
        ui_mla_rotation_lbl.grid(column=0, row=row, sticky=tk.W)
        self._ui_mla_rotation.grid(column=1, row=row, sticky=tk.EW, columnspan=2)
        ui_mla_rotation_unit.grid(column=3, row=row, sticky=tk.W)
        row += 1

        ui_mla_offset_lbl = ttk.Label(ui_tab, text='MLA offset:', anchor=tk.E)
        Hovertip(ui_mla_offset_lbl, text=self.model.cfg._mla_offset_doc)
        self._ui_mla_offset_x = ttk.Entry(
            ui_tab, textvariable=self._var_mla_offset_x)
        self._ui_mla_offset_x_tip = Hovertip(
            self._ui_mla_offset_x, text=self.model.cfg._mla_offset_doc)
        self.ui_widgets.append(self._ui_mla_offset_x)
        self._ui_mla_offset_y = ttk.Entry(
            ui_tab, textvariable=self._var_mla_offset_y)
        self._ui_mla_offset_y_tip = Hovertip(
            self._ui_mla_offset_y, text=self.model.cfg._mla_offset_doc)
        self.ui_widgets.append(self._ui_mla_offset_y)
        ui_mla_offset_unit = ttk.Label(ui_tab, text='\u00B5m')  # microns
        #
        ui_mla_offset_lbl.grid(column=0, row=row, sticky=tk.W)
        self._ui_mla_offset_x.grid(column=1, row=row, sticky=tk.EW)
        self._ui_mla_offset_y.grid(column=2, row=row, sticky=tk.EW)
        ui_mla_offset_unit.grid(column=3, row=row, sticky=tk.W)
        row += 1

        ui_focal_length_mla_lbl = ttk.Label(
            ui_tab, text='MLA focal length:', anchor=tk.E)
        Hovertip(ui_focal_length_mla_lbl, text=self.model.cfg._focal_length_mla_doc)
        self._ui_focal_length_mla = ttk.Entry(
            ui_tab, textvariable=self._var_focal_length_mla)
        self._ui_focal_length_mla_tip = Hovertip(
            self._ui_focal_length_mla, text=self.model.cfg._focal_length_mla_doc)
        self.ui_widgets.append(self._ui_focal_length_mla)
        ui_focal_length_mla_unit = ttk.Label(ui_tab, text='mm')
        #
        ui_focal_length_mla_lbl.grid(column=0, row=row, sticky=tk.W)
        self._ui_focal_length_mla.grid(column=1, row=row, sticky=tk.EW, columnspan=2)
        ui_focal_length_mla_unit.grid(column=3, row=row, sticky=tk.W)
        row += 1

        ui_focal_length_obj_lens_lbl = ttk.Label(
            ui_tab, text='Objective lens focal length:', anchor=tk.E)
        Hovertip(ui_focal_length_obj_lens_lbl,
                 text=self.model.cfg._focal_length_obj_lens_doc)
        self._ui_focal_length_obj_lens = ttk.Entry(
            ui_tab, textvariable=self._var_focal_length_obj_lens)
        self._ui_focal_length_obj_lens_tip = Hovertip(
            self._ui_focal_length_obj_lens,
            text=self.model.cfg._focal_length_obj_lens_doc)
        self.ui_widgets.append(self._ui_focal_length_obj_lens)
        ui_focal_length_obj_lens_unit = ttk.Label(ui_tab, text='mm')
        #
        ui_focal_length_obj_lens_lbl.grid(column=0, row=row, sticky=tk.W)
        self._ui_focal_length_obj_lens.grid(column=1, row=row, sticky=tk.EW, columnspan=2)
        ui_focal_length_obj_lens_unit.grid(column=3, row=row, sticky=tk.W)
        row += 1

        ui_focal_length_fourier_lens_lbl = ttk.Label(
            ui_tab, text='Fourier lens focal length:', anchor=tk.E)
        Hovertip(ui_focal_length_fourier_lens_lbl,
                 text=self.model.cfg._focal_length_fourier_lens_doc)
        self._ui_focal_length_fourier_lens = ttk.Entry(
            ui_tab, textvariable=self._var_focal_length_fourier_lens)
        self._ui_focal_length_fourier_lens_tip = Hovertip(
            self._ui_focal_length_fourier_lens,
            text=self.model.cfg._focal_length_fourier_lens_doc)
        self.ui_widgets.append(self._ui_focal_length_fourier_lens)
        ui_focal_length_fourier_lens_unit = ttk.Label(ui_tab, text='mm')
        #
        ui_focal_length_fourier_lens_lbl.grid(column=0, row=row, sticky=tk.W)
        self._ui_focal_length_fourier_lens.grid(column=1, row=row, sticky=tk.EW, columnspan=2)
        ui_focal_length_fourier_lens_unit.grid(column=3, row=row, sticky=tk.W)
        row += 1

        ui_focal_length_tube_lens_lbl = ttk.Label(
            ui_tab, text='Tube lens focal length:', anchor=tk.E)
        Hovertip(ui_focal_length_tube_lens_lbl,
                 text=self.model.cfg._focal_length_tube_lens_doc)
        self._ui_focal_length_tube_lens = ttk.Entry(
            ui_tab, textvariable=self._var_focal_length_tube_lens)
        self._ui_focal_length_tube_lens_tip = Hovertip(
            self._ui_focal_length_tube_lens,
            text=self.model.cfg._focal_length_tube_lens_doc)
        self.ui_widgets.append(self._ui_focal_length_tube_lens)
        ui_focal_length_tube_lens_unit = ttk.Label(ui_tab, text='mm')
        #
        ui_focal_length_tube_lens_lbl.grid(column=0, row=row, sticky=tk.W)
        self._ui_focal_length_tube_lens.grid(column=1, row=row, sticky=tk.EW, columnspan=2)
        ui_focal_length_tube_lens_unit.grid(column=3, row=row, sticky=tk.W)
        row += 1

        ui_num_aperture_lbl = ttk.Label(
            ui_tab, text='Objective num. aperture:', anchor=tk.E)
        Hovertip(ui_num_aperture_lbl, text=self.model.cfg._num_aperture_doc)
        self._ui_num_aperture = ttk.Entry(
            ui_tab, textvariable=self._var_num_aperture)
        self._ui_num_aperture_tip = Hovertip(
            self._ui_num_aperture, text=self.model.cfg._num_aperture_doc)
        self.ui_widgets.append(self._ui_num_aperture)
        #
        ui_num_aperture_lbl.grid(column=0, row=row, sticky=tk.W)
        self._ui_num_aperture.grid(column=1, row=row, sticky=tk.EW, columnspan=2)
        row += 1

        ui_ref_idx_immersion_lbl = ttk.Label(
            ui_tab, text='Immersion refractive index:', anchor=tk.E)
        Hovertip(ui_ref_idx_immersion_lbl, text=self.model.cfg._ref_idx_immersion_doc)
        self._ui_ref_idx_immersion = ttk.Entry(
            ui_tab, textvariable=self._var_ref_idx_immersion)
        self._ui_ref_idx_immersion_tip = Hovertip(
            self._ui_ref_idx_immersion, text=self.model.cfg._ref_idx_immersion_doc)
        self.ui_widgets.append(self._ui_ref_idx_immersion)
        #
        ui_ref_idx_immersion_lbl.grid(column=0, row=row, sticky=tk.W)
        self._ui_ref_idx_immersion.grid(column=1, row=row, sticky=tk.EW, columnspan=2)
        row += 1

        ui_ref_idx_medium_lbl = ttk.Label(
            ui_tab, text='Medium refractive index:', anchor=tk.E)
        Hovertip(ui_ref_idx_medium_lbl, text=self.model.cfg._ref_idx_medium_doc)
        self._ui_ref_idx_medium = ttk.Entry(
            ui_tab, textvariable=self._var_ref_idx_medium)
        self._ui_ref_idx_medium_tip = Hovertip(
            self._ui_ref_idx_medium, text=self.model.cfg._ref_idx_medium_doc)
        self.ui_widgets.append(self._ui_ref_idx_medium)
        #
        ui_ref_idx_medium_lbl.grid(column=0, row=row, sticky=tk.W)
        self._ui_ref_idx_medium.grid(column=1, row=row, sticky=tk.EW, columnspan=2)
        row += 1

        ui_pixel_size_camera_lbl = ttk.Label(
            ui_tab, text='Camera pixel size:', anchor=tk.E)
        Hovertip(ui_pixel_size_camera_lbl, text=self.model.cfg._pixel_size_camera_doc)
        self._ui_pixel_size_camera = ttk.Entry(
            ui_tab, textvariable=self._var_pixel_size_camera)
        self._ui_pixel_size_camera_tip = Hovertip(
            self._ui_pixel_size_camera, text=self.model.cfg._pixel_size_camera_doc)
        self.ui_widgets.append(self._ui_pixel_size_camera)
        ui_pixel_size_camera_unit = ttk.Label(ui_tab, text='\u00B5m')  # microns
        #
        ui_pixel_size_camera_lbl.grid(column=0, row=row, sticky=tk.W)
        self._ui_pixel_size_camera.grid(column=1, row=row, sticky=tk.EW, columnspan=2)
        ui_pixel_size_camera_unit.grid(column=3, row=row, sticky=tk.W)
        row += 1

        # Final padding and layout
        ui_tab.columnconfigure(index=1, weight=1)
        ui_tab.columnconfigure(index=2, weight=1)
        self.model.grid_slaves_configure(ui_tab, padx=1, pady=1)

        ui_tab.pack(anchor=tk.NW, fill=tk.X, expand=True, padx=5, pady=5)

        return self._ui_mla_type  # Control that gets initial focus

    # pylint: disable=too-many-return-statements,too-many-branches
    def validate(self) -> bool:
        if not self.is_float(self._var_mla_lens_pitch.get()):
            self.initial_focus = self._ui_mla_lens_pitch
            self._ui_mla_lens_pitch_tip.showtip()
            return False
        if not self.is_float(self._var_mla_optic_size.get()):
            self.initial_focus = self._ui_mla_optic_size
            self._ui_mla_optic_size_tip.showtip()
            return False
        if not self.is_float(self._var_mla_centre_x.get()):
            self.initial_focus = self._ui_mla_centre_x
            self._ui_mla_centre_x_tip.showtip()
            return False
        if not self.is_float(self._var_mla_centre_y.get()):
            self.initial_focus = self._ui_mla_centre_y
            self._ui_mla_centre_y_tip.showtip()
            return False
        if not self.is_float(self._var_mla_rotation.get()):
            self.initial_focus = self._ui_mla_rotation
            self._ui_mla_rotation_tip.showtip()
            return False
        if not self.is_float(self._var_mla_offset_x.get()):
            self.initial_focus = self._ui_mla_offset_x
            self._ui_mla_offset_x_tip.showtip()
            return False
        if not self.is_float(self._var_mla_offset_y.get()):
            self.initial_focus = self._ui_mla_offset_y
            self._ui_mla_offset_y_tip.showtip()
            return False
        if not self.is_float(self._var_focal_length_mla.get()):
            self.initial_focus = self._ui_focal_length_mla
            self._ui_focal_length_mla_tip.showtip()
            return False
        if not self.is_float(self._var_focal_length_obj_lens.get()):
            self.initial_focus = self._ui_focal_length_obj_lens
            self._ui_focal_length_obj_lens_tip.showtip()
            return False
        if not self.is_float(self._var_focal_length_fourier_lens.get()):
            self.initial_focus = self._ui_focal_length_fourier_lens
            self._ui_focal_length_fourier_lens_tip.showtip()
            return False
        if not self.is_float(self._var_focal_length_tube_lens.get()):
            self.initial_focus = self._ui_focal_length_tube_lens
            self._ui_focal_length_tube_lens_tip.showtip()
            return False
        if not self.is_float(self._var_num_aperture.get()):
            self.initial_focus = self._ui_num_aperture
            self._ui_num_aperture_tip.showtip()
            return False
        if not self.is_float(self._var_ref_idx_immersion.get()):
            self.initial_focus = self._ui_ref_idx_immersion
            self._ui_ref_idx_immersion_tip.showtip()
            return False
        if not self.is_float(self._var_ref_idx_medium.get()):
            self.initial_focus = self._ui_ref_idx_medium
            self._ui_ref_idx_medium_tip.showtip()
            return False
        if not self.is_float(self._var_pixel_size_camera.get()):
            self.initial_focus = self._ui_pixel_size_camera
            self._ui_pixel_size_camera_tip.showtip()
            return False

        return super().validate()

    def process(self) -> None:
        self.model.cfg.mla_type = smlfm.MicroLensArray.LatticeType[
            self._var_mla_type.get()]
        self.model.cfg.mla_lens_pitch = float(self._var_mla_lens_pitch.get())
        self.model.cfg.mla_optic_size = float(self._var_mla_optic_size.get())
        self.model.cfg.mla_centre = (  # Tuple
            float(self._var_mla_centre_x.get()),
            float(self._var_mla_centre_y.get()))
        self.model.cfg.mla_rotation = float(self._var_mla_rotation.get())
        self.model.cfg.mla_offset = (  # Tuple
            float(self._var_mla_offset_x.get()),
            float(self._var_mla_offset_y.get()))
        self.model.cfg.focal_length_mla = float(self._var_focal_length_mla.get())
        self.model.cfg.focal_length_obj_lens = (
            float(self._var_focal_length_obj_lens.get()))
        self.model.cfg.focal_length_fourier_lens = (
            float(self._var_focal_length_fourier_lens.get()))
        self.model.cfg.focal_length_tube_lens = (
            float(self._var_focal_length_tube_lens.get()))
        self.model.cfg.num_aperture = float(self._var_num_aperture.get())
        self.model.cfg.ref_idx_immersion = float(self._var_ref_idx_immersion.get())
        self.model.cfg.ref_idx_medium = float(self._var_ref_idx_medium.get())
        self.model.cfg.pixel_size_camera = float(self._var_pixel_size_camera.get())

        super().process()

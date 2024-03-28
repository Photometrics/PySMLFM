class FourierMicroscope:
    """A class describing fourier light field microscope.

    Attributes:
        num_aperture (float): A numerical aperture of the objective.
        mla_lens_pitch (float):
            A pitch along X direction, parallel with optical table (in microns).
        focal_length_mla (float):
            A focal length of micro-lens array (in mm).
        focal_length_obj_lens (float):
            A focal length of the objective lens (in mm).
        focal_length_tube_lens (float):
            A focal length of the tube lens (in mm).
        focal_length_fourier_lens (float):
            A focal length of the fourier lens (in mm).
        pixel_size_camera (float): A camera pixel size (in microns).
        ref_idx_immersion (float): An immersion refractive index.
        ref_idx_medium (float): A specimen/medium refractive index.

        bfp_radius (float):
            A radius of the conjugate back focal plane (in microns).
        bfp_lens_count (float):
            A number of micro-lenses in the conjugate back focal plane.
        pixels_per_lens (float): A number of camera pixels per micro-lens.
        magnification (float):
            An overall magnification to camera plane, from MLA lattice spacing
            units to microns.
        pixel_size_sample (float): A pixel size in sample space (in microns).
        rho_scaling (float):
            A scaling factor to convert microns in image plane to rho.

        xy_to_uv_scale (float):
            A scale factor to convert X,Y coordinates to U,V units.
        mla_to_uv_scale (float):
            A scale factor to convert MLA lens centers coordinates to U,V units.
        mla_to_xy_scale (float):
            A scale factor to convert MLA lens centers coordinates to X,Y units.
    """

    def __init__(self,
                 num_aperture: float,
                 mla_lens_pitch: float,
                 focal_length_mla: float,
                 focal_length_obj_lens: float,
                 focal_length_tube_lens: float,
                 focal_length_fourier_lens: float,
                 pixel_size_camera: float,
                 ref_idx_immersion: float,
                 ref_idx_medium: float):
        """Constructs fourier light field microscope object.

        Args:
            num_aperture (float): A numerical aperture of the objective.
            mla_lens_pitch (float):
                A pitch along X direction, parallel with optical table
                (in microns).
            focal_length_mla (float):
                A focal length of micro-lens array (in mm).
            focal_length_obj_lens (float):
                A focal length of the objective lens (in mm).
            focal_length_tube_lens (float):
                A focal length of the tube lens (in mm).
            focal_length_fourier_lens (float):
                A focal length of the fourier lens (in mm).
            pixel_size_camera (float): A camera pixel size (in microns).
            ref_idx_immersion (float): An immersion refractive index.
            ref_idx_medium (float): A specimen/medium refractive index.
        """

        self.num_aperture = num_aperture
        self.mla_lens_pitch = mla_lens_pitch
        self.focal_length_mla = focal_length_mla
        self.focal_length_obj_lens = focal_length_obj_lens
        self.focal_length_tube_lens = focal_length_tube_lens
        self.focal_length_fourier_lens = focal_length_fourier_lens
        self.pixel_size_camera = pixel_size_camera
        self.ref_idx_immersion = ref_idx_immersion
        self.ref_idx_medium = ref_idx_medium

        self.bfp_radius = (
                1000 * num_aperture * focal_length_obj_lens
                * (focal_length_fourier_lens / focal_length_tube_lens))
        self.bfp_lens_count = 2.0 * self.bfp_radius / mla_lens_pitch
        self.pixels_per_lens = mla_lens_pitch / pixel_size_camera
        self.magnification = (
                (focal_length_tube_lens / focal_length_obj_lens)
                * (focal_length_mla / focal_length_fourier_lens))
        self.pixel_size_sample = pixel_size_camera / self.magnification
        self.rho_scaling = self.magnification / self.bfp_radius

        self.xy_to_uv_scale = self.rho_scaling
        self.mla_to_uv_scale = 2.0 / self.bfp_lens_count
        self.mla_to_xy_scale = self.mla_to_uv_scale / self.xy_to_uv_scale

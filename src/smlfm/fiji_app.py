from pathlib import Path
from typing import Optional

_HAS_IMAGEJ: bool = True
try:
    import imagej
    import jpype
    import scyjava
except ImportError:
    _HAS_IMAGEJ = False


class FijiApp:

    def __init__(self):
        # One time detection during app start if PyImageJ package is installed
        self.has_imagej: bool = _HAS_IMAGEJ
        # Detected during update of CFG stage
        # Once detected, it cannot be deactivated as Java can only be started once
        self.has_fiji: bool = False
        # A path where Fiji app has been detected
        # Modified value will apply only after app restarts
        self.fiji_dir: Optional[Path] = None
        # A list with options for JVM
        # Modified value will apply only after app restarts
        self.fiji_jvm_opts: str = ''
        # ImageJ/Fiji instance, if detected
        if _HAS_IMAGEJ:
            self.ij: Optional[jpype.JClass] = None

    # Can be executed on thread
    def detect_fiji(self, fiji_dir: Path, fiji_jvm_opts: str = '') -> Optional[bool]:
        """ Returns None if Fiji has been already detected and this call
            was done with different path or JVM options. """
        if self.has_fiji:
            # Once detected, it cannot be deactivated as Java can only be started once
            if fiji_dir != self.fiji_dir or fiji_jvm_opts != self.fiji_jvm_opts:
                return None
            return True
        if not self.has_imagej:
            # PyImageJ not installed
            return False
        if fiji_dir is None:
            return False

        try:
            jvm_opts = fiji_jvm_opts.split()
            scyjava.config.add_options(jvm_opts)
            self.ij = imagej.init(str(fiji_dir), mode=imagej.Mode.INTERACTIVE)
        except RuntimeError:
            return False

        print(f'ImageJ version(s): {self.ij.getVersion()}')  # pylint: disable=no-member
        print(f'IJ app version: {self.ij.app().getVersion()}')  # pylint: disable=no-member

        self.has_fiji = True
        self.fiji_dir = fiji_dir
        self.fiji_jvm_opts = fiji_jvm_opts

        return True

    # Can be executed on thread
    def run_peakfit(self, img_stack: Path, out_csv_file: Path):
        j_stack = self.ij.io().open(str(img_stack))  # pylint: disable=no-member
        j_imp_stack = self.ij.py.to_imageplus(j_stack)  # pylint: disable=no-member

        res_dir = out_csv_file.parent

        # noinspection PyPep8Naming
        # pylint: disable=invalid-name
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

        # pylint: disable=no-member
        was_log_window_open = self.ij.WindowManager.getWindow("Log") is not None

        # Apply our configuration # pylint: disable=no-member
        self.ij.py.run_plugin('Fit Configuration', args=peakfit_args)
        # Allow user to change the configuration # pylint: disable=no-member
        self.ij.py.run_plugin('Fit Configuration')
        # Run the plugin code on given stack # pylint: disable=no-member
        self.ij.py.run_plugin('Peak Fit', args=peakfit_args, imp=j_imp_stack)

        # Close Log window if it wasn't open before Peak Fit
        if not was_log_window_open:
            # pylint: disable=no-member
            log_window = self.ij.WindowManager.getWindow("Log")
            if log_window is not None:
                log_window.setVisible(False)

        res_xls_file = res_dir / (img_stack.name + '.results.xls')
        # Rename to configured CSV file (overwrite if exists)
        res_xls_file.replace(out_csv_file)

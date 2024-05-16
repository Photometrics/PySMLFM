#!/usr/bin/env python3

import dataclasses
import pkgutil
import sys
import time
from datetime import datetime
from pathlib import Path

import numpy as np
from matplotlib import pyplot as plt

import smlfm


def app():
    tic_total = time.time()
    user_interaction_time = 0
    timestamp = datetime.now()

    # 0. Handle CLI options

    cfg_file = None
    img_stack = None
    csv_file = None
    for arg in sys.argv[1:]:
        a = arg.casefold()
        if a.endswith('.json'):
            cfg_file = Path(arg)
        elif a.endswith('.tiff') or a.endswith('.tif'):
            img_stack = Path(arg)
        elif a.endswith('.csv') or a.endswith('.xls'):
            csv_file = Path(arg)
        else:
            print(f'WARNING: Ignoring unrecognized option "{arg}"')

    # 1. Prepare configuration

    if cfg_file is not None:
        with open(cfg_file, 'rt') as file:
            cfg_dump = file.read()
    else:
        cfg_dump = pkgutil.get_data(
            smlfm.__name__, 'data/default-config.json').decode()
        print('WARNING: Loaded default configuration')

    cfg = smlfm.Config.from_json(cfg_dump)

    # CLI option takes precedence
    if img_stack is not None:
        cfg.img_stack = img_stack
    if csv_file is not None:
        cfg.csv_file = csv_file

    if cfg.img_stack is not None:
        if not cfg.img_stack.exists():
            print(f'ERROR: The image stack file "{cfg.img_stack}" does not exist')
            sys.exit(3)

        fiji_app = smlfm.FijiApp()
        if not fiji_app.has_imagej:
            print('PyImageJ not installed')
        else:
            print('Detecting Fiji...')
            fiji_app.detect_fiji(cfg.fiji_dir, cfg.fiji_jvm_opts)
            if not fiji_app.has_fiji:
                print('Fiji not detected')
            else:
                if cfg.csv_file is None:
                    cfg.csv_file = Path(str(cfg.img_stack) + '.csv')
                cfg.csv_format = smlfm.LocalisationFile.Format.PEAKFIT
                fiji_app.run_peakfit(cfg.img_stack, cfg.csv_file)

    if cfg.csv_file is None:
        print('ERROR: The CSV file not set')
        sys.exit(1)
    if not cfg.csv_file.exists():
        print(f'ERROR: The CSV file "{cfg.csv_file}" does not exist')
        sys.exit(2)

    lfm = smlfm.FourierMicroscope(
        cfg.num_aperture, cfg.mla_lens_pitch,
        cfg.focal_length_mla, cfg.focal_length_obj_lens,
        cfg.focal_length_tube_lens, cfg.focal_length_fourier_lens,
        cfg.pixel_size_camera, cfg.ref_idx_immersion,
        cfg.ref_idx_medium)

    # 2. Read localisation file

    tic = time.time()

    csv = smlfm.LocalisationFile(cfg.csv_file, cfg.csv_format)
    csv.read()

    print(f'Loaded {csv.data.shape[0]} localisations from'
          f' {np.unique(csv.data[:, 0]).shape[0]} unique frames')

    if cfg.show_graphs and cfg.show_all_debug_graphs:
        fig = smlfm.graphs.draw_locs_csv(plt.figure(), csv.data[:, 1:3])
        fig.canvas.manager.set_window_title('Raw localisations')

    csv.scale_peakfit_data(lfm.pixel_size_sample)
    locs_2d_csv = csv.data.copy()

    # Center X and Y to their means
    # TODO: Why center the data to means? Ensure how is this related to MLA centre.
    locs_2d_csv[:, 1] -= locs_2d_csv[:, 1].mean()
    locs_2d_csv[:, 2] -= locs_2d_csv[:, 2].mean()

    if cfg.log_timing:
        print(f'Loading {repr(cfg.csv_file.name)} took {1e3 * (time.time() - tic):.3f} ms')

    # 3. Prepare MLA and rotate it to match the CSV data

    mla = smlfm.MicroLensArray(
        cfg.mla_type, cfg.focal_length_mla, cfg.mla_lens_pitch,
        cfg.mla_optic_size, cfg.mla_centre)

    if cfg.show_graphs and cfg.show_all_debug_graphs:
        fig = smlfm.graphs.draw_mla(plt.figure(), mla.lens_centres, mla.centre)
        fig.canvas.manager.set_window_title('Micro-lens array centres')

    mla.rotate_lattice(np.deg2rad(cfg.mla_rotation))
    mla.offset_lattice(cfg.mla_offset / lfm.mla_to_xy_scale)  # XY -> MLA

    if cfg.show_graphs and cfg.show_all_debug_graphs:
        fig = smlfm.graphs.draw_mla(plt.figure(), mla.lens_centres, mla.centre)
        fig.canvas.manager.set_window_title('Micro-lens array centres rotated')

    # 4. Map localisations to lenses

    tic = time.time()

    lfl = smlfm.Localisations(locs_2d_csv)
    lfl.assign_to_lenses(mla, lfm)

    if cfg.log_timing:
        print(f'Mapping points to lenses took {1e3 * (time.time() - tic):.3f} ms')

    if cfg.show_graphs and cfg.show_mla_alignment_graph:
        fig = smlfm.graphs.draw_locs(
            plt.figure(),
            xy=lfl.locs_2d[:, 3:5],
            lens_idx=lfl.locs_2d[:, 12],
            lens_centres=(mla.lens_centres - mla.centre) * lfm.mla_to_xy_scale,
            # U,V values are around MLA centre but that offset is not included
            mla_centre=np.array([0.0, 0.0]))
        fig.canvas.manager.set_window_title('Localisations with lens centers')

        # Ask the user to confirm if micro-lenses are correctly aligned
        if cfg.confirm_mla_alignment:
            tic = time.time()
            print('')
            print('Check on the figure that the lenses are well aligned with the'
                  ' data. Then close the window(s) to continue.')
            print('If the alignment is incorrect, answer No in followup question,'
                  ' adjust MLA rotation and/or offset in the configuration,'
                  ' and run this application again.')
            plt.show()
            while True:
                data = input('\nAre the lens centres aligned with the data? [Y/n]: ')
                data = 'y' if data == '' else data[0].casefold()
                if data not in ('y', 'n'):
                    print('Not an appropriate choice.')
                else:
                    if data == 'n':
                        sys.exit(10)
                    break
            print('')
            user_interaction_time = time.time() - tic

    # 5. Filter localisations and set alpha model

    tic = time.time()

    if cfg.filter_lenses:
        lfl.filter_lenses(mla, lfm)
    if cfg.filter_rhos is not None:
        lfl.filter_rhos(cfg.filter_rhos)
    if cfg.filter_spot_sizes is not None:
        lfl.filter_spot_sizes(cfg.filter_spot_sizes)
    if cfg.filter_photons is not None:
        lfl.filter_photons(cfg.filter_photons)

    lfl.init_alpha_uv(cfg.alpha_model, lfm, worker_count=cfg.max_workers)

    if cfg.log_timing:
        print(f'Filtering and setting alpha model took {1e3 * (time.time() - tic):.3f} ms')

    # 6. Find system aberrations

    tic = time.time()

    fit_params_cor = dataclasses.replace(
        cfg.fit_params_aberration,
        frame_min=(cfg.fit_params_aberration.frame_min
                   if cfg.fit_params_aberration.frame_min > 0
                   else lfl.min_frame),
        frame_max=(cfg.fit_params_aberration.frame_max
                   if cfg.fit_params_aberration.frame_max > 0
                   else min(1000, lfl.max_frame)),
    )

    print(f'Fitting frames'
          f' {fit_params_cor.frame_min}-{fit_params_cor.frame_max}'
          f' for aberration correction...')
    _, fit_data = smlfm.Fitting.light_field_fit(
        lfl.filtered_locs_2d, lfm.rho_scaling, fit_params_cor,
        worker_count=cfg.max_workers)

    correction = smlfm.Fitting.calculate_view_error(
        lfl.filtered_locs_2d, lfm.rho_scaling, fit_data, cfg.aberration_params)
    # print('Global aberration calculated [\u03BCm] (u,v,dx,dy,count):')
    # with np.printoptions(precision=6, suppress=True):
    #     print(f'{correction}')

    lfl.correct_xy(correction)

    if cfg.show_graphs and cfg.show_all_debug_graphs:
        fig = smlfm.graphs.draw_locs(
            plt.figure(),
            xy=lfl.corrected_locs_2d[:, 3:5],
            lens_idx=lfl.corrected_locs_2d[:, 12],
            lens_centres=(mla.lens_centres - mla.centre) * lfm.mla_to_xy_scale,
            # U,V values are around MLA centre but that offset is not included
            mla_centre=np.array([0.0, 0.0]))
        fig.canvas.manager.set_window_title('Corrected localisations')

    if cfg.log_timing:
        print(f'Aberration correction took {1e3 * (time.time() - tic):.3f} ms')

    # 7. Fit full data set on corrected localisations

    tic = time.time()

    fit_params_all = dataclasses.replace(
        cfg.fit_params_full,
        frame_min=(cfg.fit_params_full.frame_min
                   if cfg.fit_params_full.frame_min > 0
                   else lfl.min_frame),
        frame_max=(cfg.fit_params_full.frame_max
                   if cfg.fit_params_full.frame_max > 0
                   else lfl.max_frame),
    )

    print(f'Fitting frames'
          f' {fit_params_all.frame_min}-{fit_params_all.frame_max}...')
    locs_3d, _ = smlfm.Fitting.light_field_fit(
        lfl.corrected_locs_2d, lfm.rho_scaling, fit_params_all,
        worker_count=cfg.max_workers,
        progress_func=lambda frame, min_frame, max_frame:
            print(f'Processing frame'
                  f' {frame - min_frame + 1}/{max_frame - min_frame + 1}...'))

    print(f'Total number of frames used for fitting:'
          f' {np.unique(locs_3d[:, 7]).shape[0]}')
    print(f'Total number of 2D localisations used for fitting:'
          f' {int(np.sum(locs_3d[:, 5]))}')
    print(f'Total number of 3D localisations: {locs_3d.shape[0]}')

    if cfg.log_timing:
        print(f'Complete fitting took {1e3 * (time.time() - tic):.3f} ms')

    # 8. Write the results

    if cfg.save_dir is not None and cfg.save_dir:

        timestamp_str = timestamp.strftime('%Y%m%d-%H%M%S')
        subdir_name = Path(f'3D Fitting - {timestamp_str} - {cfg.csv_file.name}')

        results = smlfm.OutputFiles(cfg, subdir_name)
        print(f'Saving results to folder: "{results.folder.name}"')

        try:
            results.mkdir()
        except Exception as ex:
            print(f'ERROR: Failed to create target folder ({repr(ex)})')
        else:
            try:
                results.save_config()
            except Exception as ex:
                print(f'ERROR: Failed to save configuration file ({repr(ex)})')
            try:
                results.save_csv(locs_3d)
            except Exception as ex:
                print(f'ERROR: Failed to save CSV file ({repr(ex)})')
            try:
                results.save_visp(locs_3d)
            except Exception as ex:
                print(f'ERROR: Failed to save ViSP file ({repr(ex)})')
            try:
                results.save_figures()
            except Exception as ex:
                print(f'ERROR: Failed to save figures file ({repr(ex)})')

    # 9. Plotting results

    if cfg.show_graphs and cfg.show_result_graphs:
        fig1, fig2, fig3 = smlfm.graphs.reconstruct_results(
            plt.figure(), plt.figure(), plt.figure(),
            locs_3d, cfg.show_max_lateral_err, cfg.show_min_view_count)
        fig1.canvas.manager.set_window_title('Occurrences')
        fig2.canvas.manager.set_window_title('Histogram')
        fig3.canvas.manager.set_window_title('3D')

    # End

    if cfg.log_timing:
        total_time = time.time() - tic_total - user_interaction_time
        print(f'Total time: {1e3 * total_time:.3f} ms')

    if cfg.show_graphs:
        plt.show()


if __name__ == '__main__':
    app()

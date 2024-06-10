from pathlib import Path

import numpy as np
import numpy.typing as npt

from .config import Config


class OutputFiles:

    CONFIG_FILE_NAME: str = 'config.json'
    CSV_FILE_NAME: str = 'locs3D.csv'
    # noinspection SpellCheckingInspection
    VISP_FILE_NAME: str = 'ViSP.3d'
    FIGURES_FILE_NAME: str = 'figures.pyw'

    def __init__(self, cfg: Config, folder: Path):
        self.cfg = cfg
        if folder.is_absolute():
            self.folder = folder
        else:
            self.folder = cfg.save_dir / folder

    def mkdir(self, mode=0o777):
        # Like POSIX 'mkdir -p'
        self.folder.mkdir(mode=mode, parents=True, exist_ok=True)

    def save_config(self):
        cfg_dump = self.cfg.to_json()
        with open(self.folder / self.CONFIG_FILE_NAME, 'wt', encoding='utf-8') as file:
            file.write(cfg_dump)

    def save_csv(self, locs_3d: npt.NDArray[float]):
        np.savetxt(self.folder / self.CSV_FILE_NAME, locs_3d,
                   fmt='%.17s,%.17s,%.17s,%.17s,%.17s,%d,%.17s,%d')

    # noinspection SpellCheckingInspection
    def save_visp(self, locs_3d: npt.NDArray[float]):
        xyz = locs_3d[:, 0:3]
        photons = locs_3d[:, 6]
        frames = locs_3d[:, 7]
        visp = np.column_stack([xyz * 1000, photons, frames])
        np.savetxt(self.folder / self.VISP_FILE_NAME, visp,
                   fmt='%.8s\t%.8s\t%.8s\t%.8s\t%d')

    def save_figures(self):
        # Generate .pyw file that shows all figures (relies on the package)
        # noinspection SpellCheckingInspection
        output_str = (
            f'#!/usr/bin/env python3\n'
            f'# # # GENERATED FILE # # #\n'
            f'from pathlib import Path\n'
            f'from matplotlib import pyplot as plt\n'
            f'import smlfm\n'
            f'if __name__ == "__main__":\n'
            f'    locs_3d = Path(__file__).parent.absolute() / "{self.CSV_FILE_NAME}"\n'
            f'    max_lat_err = {self.cfg.show_max_lateral_err}\n'
            f'    min_views = {self.cfg.show_min_view_count}\n'
            f'    fig1, fig2, fig3 = smlfm.graphs.reconstruct_results(\n'
            f'        plt.figure(), plt.figure(), plt.figure(),\n'
            f'        locs_3d, max_lat_err, min_views)\n'
            f'    fig1.canvas.manager.set_window_title("Occurrences")\n'
            f'    fig2.canvas.manager.set_window_title("Histogram")\n'
            f'    fig3.canvas.manager.set_window_title("3D")\n'
            f'    plt.show()\n'
        )
        with open(self.folder / self.FIGURES_FILE_NAME, 'wt', encoding='utf-8') as file:
            file.write(output_str)

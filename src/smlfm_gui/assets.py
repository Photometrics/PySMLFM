import pkgutil

import tksvg

from . import __name__ as _pkg_name_


class Icons:
    def __init__(self):
        # TODO: Detect high-DPI screen and adjust the scale factor
        self.svg_scale = 1.0
        self.big_number_scale = 3.0
        self._svg_big_number_scale = self.svg_scale * self.big_number_scale

        # Black filled Material icons taken from:
        # https://fonts.google.com/icons?icon.set=Material+Icons&icon.style=Filled
        self.default_size = 18  # In PX for image size, in DP for file name
        color = 'black'
        fill_hex_color = '#000000'
        mi_suffix = f'_{color}_{self.default_size}dp.svg'

        # Remaining icons taken from: https://pictogrammers.com/library/mdi/
        # These icons don't contain width and height attributes in pixels,
        # and fill value. We inject it here.
        pg_suffix = '.svg'

        def pg_inject_missing_attrs(svg_data: bytes) -> bytes:
            for attr in [b' height=', b' width=', b' fill=']:
                if attr in svg_data:
                    return svg_data  # Don't modify
            vb = 'viewBox="0 0 24 24"'
            h = f'height="{self.default_size}px"'
            w = f'width="{self.default_size}px"'
            f = f'fill="{fill_hex_color}"'
            svg_data = svg_data.replace(f' {vb}'.encode('ascii'),
                                        f' {h} {vb} {w} {f}'.encode('ascii'),
                                        1)
            return svg_data

        # This hack crops the number icons and enforces their real minimal size
        def pg_crop_number_icon(svg_data: bytes) -> bytes:
            for attr in [b' viewBox=', b' height=', b' width=']:
                if attr not in svg_data:
                    return svg_data  # Don't modify
            vb1 = 'viewBox="0 0 24 24"'
            vb2 = 'viewBox="6 6 12 12"'
            h1 = f'height="{self.default_size}px"'
            w1 = f'width="{self.default_size}px"'
            h2 = 'height="12px"'
            w2 = 'width="12px"'
            svg_data = svg_data.replace(f' {vb1}'.encode('ascii'),
                                        f' {vb2}'.encode('ascii'),
                                        1)
            svg_data = svg_data.replace(f' {h1}'.encode('ascii'),
                                        f' {h2}'.encode('ascii'),
                                        1)
            svg_data = svg_data.replace(f' {w1}'.encode('ascii'),
                                        f' {w2}'.encode('ascii'),
                                        1)
            return svg_data

        # Color palette for icons generated at:
        # https://coolors.co/d19c1d-613a3a-9d75cb-118ab2-26c485-db2955
        color_app = '#D19C1D'  # Goldenrod (yellow-like)
        color_any = '#613A3A'  # Rose ebony (brown-like)
        color_settings = '#9D75CB'  # Amethyst (violet-like)
        color_preview = '#118AB2'  # Blue (NCS)
        color_start = '#26C485'  # Emerald (green-like)
        color_cancel = '#DB2955'  # Raspberry (red-like)

        def replace_color(svg_data: bytes, new_hex_color: str,
                          old_hex_color: str = fill_hex_color) -> bytes:
            svg_data = svg_data.replace(f'fill="{old_hex_color}"'.encode('ascii'),
                                        f'fill="{new_hex_color}"'.encode('ascii'),
                                        1)
            return svg_data

        # Material icons

        data = pkgutil.get_data(_pkg_name_, f'data/hive{mi_suffix}')
        data = replace_color(data, color_app)
        self.app = tksvg.SvgImage(data=data, scale=self.svg_scale)

        data = pkgutil.get_data(_pkg_name_, f'data/folder_open{mi_suffix}')
        data = replace_color(data, color_any)
        self.open = tksvg.SvgImage(data=data, scale=self.svg_scale)

        data = pkgutil.get_data(_pkg_name_, f'data/save{mi_suffix}')
        data = replace_color(data, color_any)
        self.save = tksvg.SvgImage(data=data, scale=self.svg_scale)

        data = pkgutil.get_data(_pkg_name_, f'data/save_as{mi_suffix}')
        data = replace_color(data, color_any)
        self.save_as = tksvg.SvgImage(data=data, scale=self.svg_scale)

        data = pkgutil.get_data(_pkg_name_, f'data/settings{mi_suffix}')
        data = replace_color(data, color_settings)
        self.settings = tksvg.SvgImage(data=data, scale=self.svg_scale)

        data = pkgutil.get_data(_pkg_name_, f'data/play_arrow{mi_suffix}')
        data = replace_color(data, color_start)
        self.start = tksvg.SvgImage(data=data, scale=self.svg_scale)

        data = pkgutil.get_data(_pkg_name_, f'data/cancel{mi_suffix}')
        data = replace_color(data, color_cancel)
        self.cancel = tksvg.SvgImage(data=data, scale=self.svg_scale)

        data = pkgutil.get_data(_pkg_name_, f'data/visibility{mi_suffix}')
        data = replace_color(data, color_preview)
        self.preview = tksvg.SvgImage(data=data, scale=self.svg_scale)

        data = pkgutil.get_data(_pkg_name_, f'data/construction{mi_suffix}')
        data = replace_color(data, color_any)
        self.cfg_stage = tksvg.SvgImage(data=data, scale=self.svg_scale)

        data = pkgutil.get_data(_pkg_name_, f'data/scatter_plot{mi_suffix}')
        data = replace_color(data, color_any)
        self.csv_stage = tksvg.SvgImage(data=data, scale=self.svg_scale)

        data = pkgutil.get_data(_pkg_name_, f'data/table_rows{mi_suffix}')
        data = replace_color(data, color_any)
        self.csv_data = tksvg.SvgImage(data=data, scale=self.svg_scale)

        data = pkgutil.get_data(_pkg_name_, f'data/collections{mi_suffix}')
        data = replace_color(data, color_any)
        self.csv_stack = tksvg.SvgImage(data=data, scale=self.svg_scale)

        data = pkgutil.get_data(_pkg_name_, f'data/search{mi_suffix}')
        data = replace_color(data, color_any)
        self.csv_peakfit = tksvg.SvgImage(data=data, scale=self.svg_scale)

        data = pkgutil.get_data(_pkg_name_, f'data/biotech{mi_suffix}')
        data = replace_color(data, color_any)
        self.opt_stage = tksvg.SvgImage(data=data, scale=self.svg_scale)

        data = pkgutil.get_data(_pkg_name_, f'data/filter_alt{mi_suffix}')
        data = replace_color(data, color_any)
        self.flt_stage = tksvg.SvgImage(data=data, scale=self.svg_scale)

        data = pkgutil.get_data(_pkg_name_, f'data/panorama_horizontal_select{mi_suffix}')
        data = replace_color(data, color_any)
        self.cor_stage = tksvg.SvgImage(data=data, scale=self.svg_scale)

        data = pkgutil.get_data(_pkg_name_, f'data/mediation{mi_suffix}')
        data = replace_color(data, color_any)
        self.fit_stage = tksvg.SvgImage(data=data, scale=self.svg_scale)

        data = pkgutil.get_data(_pkg_name_, f'data/bar_chart{mi_suffix}')
        data = replace_color(data, color_preview)
        self.fit_occurrences = tksvg.SvgImage(data=data, scale=self.svg_scale)

        data = pkgutil.get_data(_pkg_name_, f'data/apps{mi_suffix}')
        data = replace_color(data, color_preview)
        self.fit_histogram = tksvg.SvgImage(data=data, scale=self.svg_scale)

        # Pictogrammers icons

        data = pkgutil.get_data(_pkg_name_, f'data/numeric-1{pg_suffix}')
        data = pg_inject_missing_attrs(data)
        data = pg_crop_number_icon(data)
        data = replace_color(data, color_app)
        self.nr1_large = tksvg.SvgImage(data=data, scale=self._svg_big_number_scale)

        data = pkgutil.get_data(_pkg_name_, f'data/numeric-2{pg_suffix}')
        data = pg_inject_missing_attrs(data)
        data = pg_crop_number_icon(data)
        data = replace_color(data, color_app)
        self.nr2_large = tksvg.SvgImage(data=data, scale=self._svg_big_number_scale)

        data = pkgutil.get_data(_pkg_name_, f'data/numeric-3{pg_suffix}')
        data = pg_inject_missing_attrs(data)
        data = pg_crop_number_icon(data)
        data = replace_color(data, color_app)
        self.nr3_large = tksvg.SvgImage(data=data, scale=self._svg_big_number_scale)

        data = pkgutil.get_data(_pkg_name_, f'data/numeric-4{pg_suffix}')
        data = pg_inject_missing_attrs(data)
        data = pg_crop_number_icon(data)
        data = replace_color(data, color_app)
        self.nr4_large = tksvg.SvgImage(data=data, scale=self._svg_big_number_scale)

        data = pkgutil.get_data(_pkg_name_, f'data/numeric-5{pg_suffix}')
        data = pg_inject_missing_attrs(data)
        data = pg_crop_number_icon(data)
        data = replace_color(data, color_app)
        self.nr5_large = tksvg.SvgImage(data=data, scale=self._svg_big_number_scale)

        data = pkgutil.get_data(_pkg_name_, f'data/numeric-6{pg_suffix}')
        data = pg_inject_missing_attrs(data)
        data = pg_crop_number_icon(data)
        data = replace_color(data, color_app)
        self.nr6_large = tksvg.SvgImage(data=data, scale=self._svg_big_number_scale)

        data = pkgutil.get_data(_pkg_name_, f'data/circle-small{pg_suffix}')
        data = pg_inject_missing_attrs(data)
        data = replace_color(data, color_preview)
        self.opt_dot = tksvg.SvgImage(data=data, scale=self.svg_scale)

        data = pkgutil.get_data(_pkg_name_, f'data/dots-hexagon{pg_suffix}')
        data = pg_inject_missing_attrs(data)
        data = replace_color(data, color_preview)
        self.opt_hexagon = tksvg.SvgImage(data=data, scale=self.svg_scale)

        data = pkgutil.get_data(_pkg_name_, f'data/dots-grid{pg_suffix}')
        data = pg_inject_missing_attrs(data)
        data = replace_color(data, color_preview)
        self.opt_square = tksvg.SvgImage(data=data, scale=self.svg_scale)

        data = pkgutil.get_data(_pkg_name_, f'data/dots-triangle{pg_suffix}')
        data = pg_inject_missing_attrs(data)
        data = replace_color(data, color_preview)
        self.opt_triangle = tksvg.SvgImage(data=data, scale=self.svg_scale)

        data = pkgutil.get_data(_pkg_name_, f'data/rotate-orbit{pg_suffix}')
        data = pg_inject_missing_attrs(data)
        data = replace_color(data, color_preview)
        self.fit_3d = tksvg.SvgImage(data=data, scale=self.svg_scale)

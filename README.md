# Single Molecule Light Field Microscopy Reconstruction (PySMLFM)

[![GitHub release](https://img.shields.io/github/v/release/Photometrics/PySMLFM?label=GitHub%20stable&color=green)](https://github.com/Photometrics/PySMLFM/releases "GitHub stable release")
[![GitHub release](https://img.shields.io/github/v/release/Photometrics/PySMLFM?include_prereleases&label=GitHub%20latest)](https://github.com/Photometrics/PySMLFM/releases "GitHub latest release")  
[![PyPI release](https://img.shields.io/pypi/v/PySMLFM?label=PyPI&&color=green)](https://pypi.org/project/PySMLFM/ "PyPI release")
[![TestPyPI release](https://img.shields.io/pypi/v/PySMLFM?pypiBaseUrl=https%3A%2F%2Ftest.pypi.org&label=TestPyPI)](https://test.pypi.org/project/PySMLFM/ "TestPyPI release")  
[![Tests status](https://github.com/Photometrics/PySMLFM/actions/workflows/tests.yml/badge.svg)](https://github.com/Photometrics/PySMLFM/actions/workflows/tests.yml "Tests status")
[![Python version from PEP 621 TOML](https://img.shields.io/python/required-version-toml?tomlFilePath=https%3A%2F%2Fraw.githubusercontent.com%2FPhotometrics%2FPySMLFM%2Fmain%2Fpyproject.toml)](https://python.org "Python versions")  
[![Average time to resolve an issue](http://isitmaintained.com/badge/resolution/Photometrics/PySMLFM.svg)](http://isitmaintained.com/project/Photometrics/PySMLFM "Average time to resolve an issue")
[![Percentage of issues still open](http://isitmaintained.com/badge/open/Photometrics/PySMLFM.svg)](http://isitmaintained.com/project/Photometrics/PySMLFM "Percentage of issues still open")
---

A Python solution inspired by MATLAB scripts in
[hexSMLFM](https://github.com/TheLeeLab/hexSMLFM) project.

> This 3D reconstruction code accompanies the preprint titled
"[High-density volumetric super-resolution microscopy](
https://www.biorxiv.org/content/10.1101/2023.05.02.539032v1)".
In brief, 2D localisation data (x,y) captured using a (square or hexagonal)
fourier light field microscope are turned into 3D localisations (x,y,z).
It does this by first assigning (x,y) to (x,y,u,v) space and using microscope
parameters to calculate z position via parallax. For more information, see:
[R. R. Sims, *et al.* Optica, 2020, 7, 1065](https://doi.org/10.1364/OPTICA.397172).

## Getting Started

Although this project is pure Python, one of its optional features talks to
[ImageJ/Fiji](https://imagej.net/) via [PyImageJ](https://github.com/imagej/pyimagej)
wrapper and uses PeakFit from [GDSC SMLM2](https://imagej.net/plugins/gdsc-smlm2)
plugin. That basically defines main requirements as well as restrictions for
this project.

If you don't plan to use PeakFit directly from this project, feel free to
configure your Python environment in a way you are used to. You can still
follow the instruction below, just skip installation of PyImageJ and OpenJDK.

Following instructions assume you don't have Python installed yet and focuses to
Windows platform only.

## Initial Setup

Initial setup follows PyImageJ instructions.

PyImageJ should be installed using [Conda](https://conda.io/) +
[Mamba](https://mamba.readthedocs.io/).
You can also `pip install pyimagej`, but will then need to install
[OpenJDK](https://en.wikipedia.org/wiki/OpenJDK) and
[Maven](https://maven.apache.org/) manually.

1. Install [Miniforge3](https://github.com/conda-forge/miniforge#miniforge3)
   to get whole Python environment. When asked how to install, select _Just me_,
   because _All users_ option would only complicate system-wide installation.
   If you really need to share the installation with other users, select
   location everybody can access and manually copy there also a Start menu
   shortcut to Miniforge prompt created by installer for you only.
2. Run Miniforge Prompt from Start menu. It opens in your home folder by default
   (e.g. `C:\Users\Me`).
3. Create new isolated virtual environment for this project (with name _MyEnv_)
   to not clutter dependencies with your existing or new projects:
   ```
   (base) C:\Users\Me> mamba create -n MyEnv -c conda-forge python=3.8 pyimagej openjdk=8
   ```
   This command will install PyImageJ with OpenJDK 8 in new virt. env. using
   Python 3.8 (the minimal Python version required).<br>
   If you don't want PyImageJ, remove last two package names from the command
   to get clean environment.<br>
   Adjust Python version if needed.

   > Note:<br>
   > If you have an AMD processor and experience low performance compared to
   > similar Intel CPU, installing an alternative BLAS library could help.
   > For example, to initialize new environment with BLIS library run:
   > ```
   > (base) C:\Users\Me> mamba create -n MyEnv -c conda-forge python=3.8 pyimagej openjdk=8 blas=*=blis
   > ```
4. **Whenever you want to use _MyEnv_ environment, activate it first**:
   ```
   (base) C:\Users\Me> mamba activate MyEnv
   ```
5. Ensure conda-forge is the first update channel:
   ```
   (MyEnv) C:\Users\Me> conda config --add channels conda-forge
   (MyEnv) C:\Users\Me> conda config --set channel_priority strict
   ```
6. Download [Fiji](https://imagej.net/software/fiji/) from official source,
   unpack it, run `ImageJ-win64.exe` and install '_GDSC&nbsp;SMLM2_' plugin via
   _Help_&#8209;>_Update..._ menu.

## Install PySMLFM

Install either stable release or development version as shown below.

### Latest Stable Release

-  Install the package from Python Package Index (PyPI):
   ```
   (MyEnv) C:\Users\Me> pip install PySMLFM
   ```

### Latest Development Version

-  Get the ZIP archive with sources from GitHub (`PySMLFM-main.zip`).
-  Install the package from source archive extracted e.g. in your home folder
   (`C:\Users\Me\PySMLFM-main`):
   ```
   (MyEnv) C:\Users\Me> cd PySMLFM-main
   (MyEnv) C:\Users\Me\PySMLFM-main> pip install .
   ```

## Execution

There are two ways how to run an application installed by this project -
by running a Python command from Miniforge Prompt or via installed `.exe`
helper script.

### Via Python Command

Run the command line application:
```
(MyEnv) C:\Users\Me> python -m smlfm_cli
```
or the GUI application:
```
(MyEnv) C:\Users\Me> python -m smlfm_gui
```

### Via Helper Script

During the installation is created a helper script that simplifies the execution
of the application. It is a self-extracting ZIP file that executes similar
command as above but uses for it the `python.exe` from the virt. env. where it
was created from. Because of that, the EXE helper works only on the that
computer and cannot be shared with anyone else, but it can be copied anywhere on
your computer.

Simply run it with:
```
(MyEnv) C:\Users\Me> smlfm-cli
```
or:
```
(MyEnv) C:\Users\Me> smlfm-gui
```
Notice the dash in the command name, it is not an underscore.

## Usage

If you already tried running the CLI application, you saw an error message.
It is because the CLI application requires one or two options as input.

### Configuration

The type of the input option is detected automatically from given file extension:
- A configuration with `.json` file extension.<br>
  It contains all possible parameters for the localisation process, output
  location, graphs to show, etc. If not specified, a default configuration file
  is used. As a starting point, make your own copy and modify the parameters
  accordingly. See
  `C:\Users\Me\miniforge\envs\MyEnv\Lib\site-packages\smlfm\data\default-config.json`.
- A 2D localisations with `.csv` or `.xls` file extension.<br>
  If not specified on command line, the path to the file must be set in the
  configuration file under `csv_file` key.<br>
  By default the CSV is expected in the format generated by PeakFit plugin
  in ImageJ/Fiji. A few other formats are supported, namely Thunderstorm and
  Picasso. Adjust the configuration file key `csv_format` where the value is
  all in upper-case.

For example, run the application with customized configuration and data, all
stored `C:\MyExperiment` folder:
   ```
   (MyEnv) C:\MyExperiment> python -m smlfm_cli my-config.json my-localisations.csv
   ```

For quick access to the EXE helper script without opening command prompt you can
create a shortcut on the desktop or in your experiment folder.
Open the path with `smlfm-cli.exe` in File Explorer (by default it is in
`C:\Users\Me\miniforge\envs\MyEnv\Scripts\ `), drag the EXE file with
mouse and drop it on the desktop or target folder while holding the `Alt` key.<br>
The shortcut has working directory set by default to the folder with the EXE file.
It is recommended changing it to a location where you want the results to be
stored. Right-click on the shortcut, select _Properties_ and modify '_Start in:_'
box accordingly. Also don't forget to add the input options at the end of the
command in the '_Target:_' box. Now you can double-click the shortcut anytime
you want to re-run the 3D localisation.

### Processing

With valid configuration the 2D localisation data is loaded from CSV file and
every localisation point is assigned to the nearest lens from micro-lens array.
With default configuration the localisations and lens centres are shown in form
of 2D graph. The user can visually check the alignment. To continue, the graph
window must be closed and then the user must either confirm the alignment or
abort the process to adjust the configuration to fix the alignment. Simply
follow the instructions in the command prompt window.

Based on the amount of input localisations and computer performance, the
processing can take from a few seconds to minutes or even hours. The command
prompt window prints a message about the progress every 1000 frames processed.

### Results

If everything completed successfully, three graphs with results are shown and
the results are stored in the disk. In the _current working directory_
(e.g. `C:\MyExperiment`) is created a subdirectory for every execution.
The subdirectory name starts with `3D Fitting ` prefix followed by a timestamp
and a CSV filename used.<br>
Each folder contains JSON configuration file used (`config.json`), calculated
3D localisations (`locs3D.csv`), an output for
[ViSP viewer](https://www.nature.com/articles/nmeth.2566) (`ViSP.3d`) and
a Python script (`figures.pyw`) that reconstructs exactly the results graphs at
any time later without a need to start the processing from beginning.

To open the saved figures run a command that takes relative path to it like this
(quote the path with spaces):
```
   (MyEnv) C:\MyExperiment> python "3D Fitting - 20240213-203318 - my-localisations.csv/figures.pyw"
```
When you use `python` command like above, the prompt will be blocked until all
graphs are closed. To open the figures without blocking the prompt use `pythonw`
instead.

## Screenshots

### Main Window

![Main Window](https://raw.githubusercontent.com/Photometrics/PySMLFM/main/images/app-gui.png)

### Optics Settings Dialog

![Optics Settings Dialog](https://raw.githubusercontent.com/Photometrics/PySMLFM/main/images/config-optics.png)

### Micro Lens Array Layout

![Micro Lens Array Layout](https://raw.githubusercontent.com/Photometrics/PySMLFM/main/images/graph-mla.png)

### Filtered Localisations

![Filtered Localisations](https://raw.githubusercontent.com/Photometrics/PySMLFM/main/images/graph-locs-filtered.png)

### 3D Reconstruction

![3D Reconstruction](https://raw.githubusercontent.com/Photometrics/PySMLFM/main/images/graph-3d.png)

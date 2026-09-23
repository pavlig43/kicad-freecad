# TrueLib for KiCad 10 and FreeCAD

Shared symbols, footprints, and STEP models. The clone can live anywhere on Windows, Linux, or macOS. KiCad uses the `TRUE_LIB` path variable to find the files.

## Install

Install KiCad 10 and open it once so it creates its global library tables. Close KiCad before running the installer. Python 3.10 or newer is required.

```sh
git clone https://github.com/pavlig43/kicad-freecad.git
cd kicad-freecad
```

On Windows PowerShell, run `.\install.cmd`. On Linux or macOS, run `python3 scripts/install.py`. The installer finds the clone from its own location and registers the `TrueLib` symbol and footprint libraries for all KiCad projects. It backs up each changed KiCad settings file first. If another library already uses the name `TrueLib`, it stops without changing settings.

To inspect the settings without changing them, run `.\install.cmd --check` on Windows PowerShell or `python3 scripts/install.py --check` on Linux or macOS. Exit code 0 means the library is set up; 1 means setup or a path update is needed; 2 means an error.

Restart KiCad after installation. The four symbols appear under `TrueLib`, and nine footprints each link to a STEP model. One symbol has no footprint link in the source and remains unlinked.

## Update

```sh
git pull
```

Run the installer again if you move the clone. Routine `git pull` updates do not require setup again.

## Files

- `kicad/TrueLib.kicad_sym`: four symbols
- `kicad/TrueLib.pretty/`: nine footprints
- `kicad/TrueLib.3dshapes/`: nine STEP models
- `freecad/`: reserved for future FreeCAD 1.1 sources

The installer changes only KiCad 10 user settings. It leaves project files and other libraries intact.

## License

MIT. See [LICENSE](LICENSE).

# HYLANDBOOK

Log your Schedule I progress.
SAVEGAME_PATH is required, optional arguments will use their defaults if not set by you.
PATH for --data-dir must not exist before you start the tool, but you will be asked for confirmation before it gets created automatically.

I last tested this on game version 0.4.0f5.

**Tool and documentation still work in progress!**


## Dependecies

**Users**:  
None if you use the pre-built executables or run it directly from the source.

**Developers**:
To install the development dependencies (optimally in a virtual Python environment), run [install_pyreq.cmd](./install_pyreq.cmd) from the repository root.  
To built the executable, run [bakedist.cmd](./bakedist.cmd).


## Usage in a nutshell

1. Download the latest release.
2. Run it.
3. Use the generated data for something, for example the .html file as overlay in OBS, or the .csv to create charts in a spreadsheet app.


## Usage overview

```text
usage: hylandbook [-h] [-d PATH] [-i SECONDS] SAVEGAME_PATH

Log your Schedule I progress. SAVEGAME_PATH is required,
optional arguments will use their defaults if not set by you.
PATH for --data-dir must not exist before you start the tool,
but you will be asked for confirmation before it gets created automatically.
I last tested this on game version 0.4.0f5.

positional arguments:
  SAVEGAME_PATH         path to a Schedule I 'SaveGame_*' directory, 
                        enclose it in quotes if it contains spaces, 
                        e.g. "C:\path to\SaveGame_1"

options:
  -h, --help            show this help message and exit

  -d, --data-dir PATH   path to directory where the logged data will be stored, 
                        default: D:\wip\hylandbook\hb_data
  
  -i, --check-interval SECONDS
                        how frequently to check the save data for changes, in seconds, 
                        default: 60, minimum: 30
```

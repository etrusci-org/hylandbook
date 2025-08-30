# HYLANDBOOK

**Tool and documentation still work in progress!**

Log your Schedule I progress.  
The main thing this tool does is logging save game data to a local SQLite database. It also generates some additional data files you can use for various things, for example the .html file as streaming overlay, or the .csv to create charts in a spreadsheet app.

I last tested this on game version 0.4.0f5.  

[Demo video](https://example.org)



## Dependecies

**Users**:  
None if you use the [pre-built executables](./dist).  
If you want to run it directly from the [source](./src), [Python](https://python.org) is needed.

**Developers**:
To install the development dependencies (optimally in a virtual Python environment), run [install_pyreq.cmd](./install_pyreq.cmd).  
To build the executable, run [bakedist.cmd](./bakedist.cmd).


## Usage in a nutshell

1. Download the latest release.
2. Run it.
3. Use the generated data for something, for example the .html file as overlay in OBS, or the .csv to create charts in a spreadsheet app.

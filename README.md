# HYLANDBOOK
> last tested on game version 0.4.0f5
> *tool and documentation still work in progress!*

Log your Schedule I progress to a local SQLite database.

Currently the following save data values are collected:
- Save data directory name
- OrganisationName
- Seed
- GameVersion
- Playtime
- ElapsedDays
- OnlineBalance
- Networth
- LifetimeEarnings
- Rank
- Tier
- XP
- TotalXP
- DiscoveredProducts *(count)*
- Vehicles *(count)*


## Dependecies

**Users**:  
None if you use the [pre-built executables](./dist).  
If you want to run it directly from the [source](./src), [Python](https://python.org) is needed.

**Developers**:  
To install the development dependencies (optimally in a virtual Python environment), run [install_pyreq.cmd](./install_pyreq.cmd).  
To build the executable, run [bakedist.cmd](./bakedist.cmd).

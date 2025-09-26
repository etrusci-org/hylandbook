# HYLANDBOOK - Changelog




## Unreleased | Work in progress

**IMPORTANT**:  
Previous v1.0.0 databases are not compatible, but you can update them to this version and keep your previous data (see "Update previous database" below).  
Further you must also edit your custom `run_hylandbook.cmd` if you were using the `-e, --export-types` option.

**New log data**  
The following new save data values are logged:
- cash balance
- owned businesses count
- owned properties count

**History export**  
Additionally to the *current* exports, you can now also export the *history* of your data.  
The new options are:

`-y, --export-history`  
One or more types of *history* export files to update each time save data changes are detected.  
Default: no export  
Choices: `json` `csv`

`-m, --history-limit`  
Limit the number of recent entries that are exported in history export files.  
Default: no limit  
Minimum: `1`

**HTML exports**  
There is a new HTML format available for both *current* and *history* exports. It will give advanced users a simple base for creating cool overlays.  
For example, if you use `--export-current html`, two files will be created. One will be `current.html` and the other `current_template.html`.  
Changes you make in `current_template.html` will be reflected in `current.html` each time save data changes are detected.  
In `current.html`, `{HB_DATA}` will be replaced with the *current* data.  
To reset the template to its default state, delete it and it will be created on the next startup.  
Same process for *history* HTML exports.

**Renamed options**  
Renamed the *current* export option `-e, --export-types` to `-c, --export-current`.

**Updated starter script**  
Updated `run_hylandbook.cmd` with renamed option.

**Export files placeholders**  
Placeholer export files will now be created on the first successfull startup before monitoring starts, if they are selected with with options, e.g. `-c txt`. Although they will contain only dummy data, it may be useful for when you need the path in advance for a tool like OBS Studio or such.

**While monitoring**  
- Reduced the precision of displayed timestamps.
- The difference of changed numbers will now be displayed too. E.g. `3.0 -> 4.2 (1.2)`.
- Showing which files were updated during the check.
- The database file is not opened during the whole process anymore but only during the actual data check. May be useful if you programmatically access it with other tools while monitoring.

**Update previous database to this version**  

- With the updater:  
  Save `update_v1.0.0_database_to_next.exe` in the same folder where your previous v1.0.0 `book.db` file is saved. Then run it (double-click) and follow the instructions.
- Manually:
  ```sql
  > sqlite3 hb_data\book.db
  ALTER TABLE logs ADD COLUMN 'cashbalance' REAL DEFAULT NULL;
  ALTER TABLE logs ADD COLUMN 'ownedbusinesses' INTEGER DEFAULT NULL;
  ALTER TABLE logs ADD COLUMN 'ownedproperties' INTEGER DEFAULT NULL;
  > .exit
  ```




## v1.0.0 | 2025-09-07

First stable release.  
Let me know if something is unclear in the README or if you encounter any bugs.  
Current state is how I use it. Your feedback/ideas are welcome.  
Enjoy :)

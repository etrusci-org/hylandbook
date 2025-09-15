# HYLANDBOOK - Changelog




## Unreleased / Work in progress

**New log data**  
The following new values are logged:
- cashbalance
- ownedbusinesses (count)
- ownedproperties (count)

**Renamed options**  
<!--
['-e', '--export-types']
to
['-c', '--export-current']
-->

**History export**  
<!--
['-y', '--export-history']
['-m', '--history-limit']
-->

**Updated starter script with new options**  
<!--
run_hylandbook.cmd
-->

**Export files placeholders**  
Placeholer export files will now be created on the first successfull startup before monitoring starts. Although they will contain only dummy data, it may be useful for when you need the path in advance for a tool like OBS Studio or such.

**While monitoring**  
- Precision of displayed timestamps is not reduced anymore.
- The difference of changed numbers will now be displayed too. E.g. `3.0 -> 4.2 (1.2)`.
- The database file is not opened during the whole process anymore but only during the actual data check. May be useful if you programmatically access it with other tools while monitoring.

**Update previous database to this version**  
Previous v1.0.0 databases are not compatible, but you can update them to this version and keep your previous data.

- With the updater:  
  Save `update_v1.0.0_database_to_next.exe` in the same folder where the v1.0.0 `book.db` file is saved.  
  Then run it (double-click) and follow the instructions.
- Manually:
  ```sql
  > sqlite3 hb_data\book.db

  ALTER TABLE logs ADD COLUMN 'cashbalance' REAL DEFAULT NULL;
  ALTER TABLE logs ADD COLUMN 'ownedbusinesses' INTEGER DEFAULT NULL;
  ALTER TABLE logs ADD COLUMN 'ownedproperties' INTEGER DEFAULT NULL;

  > .exit
  ```




## v1.0.0 / 2025-09-07

First stable release.  
Let me know if something is unclear in the [README](./README.md) or if you encounter any bugs.  
Current state is how I use it. Your feedback/ideas are welcome.  
Enjoy :)

# HYLANDBOOK - Changelog


## Unreleased

**New log data:**
- cashbalance
- ownedbusinesses
- ownedproperties

**Export file placeholders will now be created one the first run.**

**Previous database files are not compatible** unless you alter them manually:
```sql
> sqlite3 hb_data\book.db

ALTER TABLE logs ADD COLUMN 'cashbalance' REAL DEFAULT NULL;
ALTER TABLE logs ADD COLUMN 'ownedbusinesses' INTEGER DEFAULT NULL;
ALTER TABLE logs ADD COLUMN 'ownedproperties' INTEGER DEFAULT NULL;

> .exit
```


## v1.0.0  | 2025-09-07

First stable release.

Let me know if something is unclear in the [README](./README.md) or if you encounter any bugs.

Current state is how I use it. Your feedback/ideas are welcome.

Enjoy :)

'''
HYLANDBOOK

Script to update v1.0.0 database to the next (not necessarily the latest) version.
See <https://github.com/etrusci-org/hylandbook/releases> for release history.

Usage: update_v1.0.0_database_to_next.py [PATH_TO_DATABASE_FILE]
'''

import os
import sqlite3
import subprocess
import sys
from pathlib import Path




def main():
    _clear_screen()

    DEFAULT_DB_FILE: Path = Path.cwd() / 'book.db'

    db_file: Path

    if len(sys.argv) < 2:
        db_file = DEFAULT_DB_FILE
    else:
        db_file = Path(sys.argv[1]).resolve()

    print(f"Expected database file path: {db_file}")

    if not db_file.exists() or not db_file.is_file():
        print("Database file does not exist on the expected path or is not a file\n")
        _prompt_to_exit(1)
    else:
        print("Database file found\n")

    if input("Are you sure this is a v1.0.0 database? [y/n]: ").strip().lower() != 'y':
        _prompt_to_exit(0)

    if input("Do you want to update it to next version now? [y/n]: ").strip().lower() != 'y':
        _prompt_to_exit(0)


    print("\nUpdating ...")

    con = sqlite3.connect(database=db_file)
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    try:
        print("> add column cashbalance")
        cur.execute("ALTER TABLE logs ADD COLUMN 'cashbalance' REAL DEFAULT NULL;")
        print("> add column ownedbusinesses")
        cur.execute("ALTER TABLE logs ADD COLUMN 'ownedbusinesses' INTEGER DEFAULT NULL;")
        print("> add column ownedproperties")
        cur.execute("ALTER TABLE logs ADD COLUMN 'ownedproperties' INTEGER DEFAULT NULL;")
        con.commit()
    except Exception as e:
        print("\nBOO:")
        print(f"* {e}")
    else:
        print("\nOK")
    finally:
        con.close()
        _prompt_to_exit()


def _clear_screen() -> None:
    if os.name == 'nt':
        subprocess.run(['cls'], shell=True)
    elif os.name == 'posix':
        subprocess.run(['/usr/bin/clear'], shell=True)
    else:
        print('\033c', end='')


def _prompt_to_exit(exit_code: int = 0, /) -> None:
    try:
        input("\npress [Enter] to exit")
    except KeyboardInterrupt:
        pass
    finally:
        sys.exit(exit_code)




if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass

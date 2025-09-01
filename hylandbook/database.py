import sqlite3
from pathlib import Path




class DatabaseSQLite:
    file: Path


    def __init__(self, file: Path) -> None:
        self.file = file


    def connect(self) -> tuple[sqlite3.Connection, sqlite3.Cursor]:
        con = sqlite3.connect(database=self.file)
        cur = con.cursor()
        return (con, cur)


    def vacuum(self) -> None:
        con, cur = self.connect()
        cur.execute('VACUUM;')
        con.close()

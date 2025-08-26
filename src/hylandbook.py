'''
DEV BRAIN

- use only python std lib
- remember that some data is not available until we left the prologue
- data parsing must handle suddenly missing variables gracefully (e.g. after a game update that changed save data struct)
'''

import argparse
import datetime
import json
import os
import sqlite3
import subprocess
import sys
import time
from pathlib import Path




# CONFIGURATION
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

BANNER: str = '-=[ H Y L A N D B O O K ]=-'
# LAST_COMPAT_VERSION: str = '0.3.6f6'
DEFAULT_DATA_DIR: Path = Path.cwd() / 'hb_data'
CHECK_INTERVAL: int = 60
SD_THROTTLE: float = 0
ARGPARSER_CONF: dict = {
    'init': {
        'prog': 'hylandbook',
        'description': 'Log your Schedule I progress.',
    },
    'args': [
        {
            'name_or_flags': ['save_dir'],
            'conf': {
                'metavar': 'SAVEGAME_DIR',
                'type': str,
                'default': None,
                'help': 'path to a Schedule I `SaveGame_*` directory',
            },
        },
        {
            'name_or_flags': ['-d', '--data-dir'],
            'conf': {
                'metavar': 'PATH',
                'type': str,
                'default': DEFAULT_DATA_DIR,
                'help': f'path to directory where hylandbook will store its data - default: {DEFAULT_DATA_DIR}',
            },
        },
    ],
}
DB_SCHEMA: str = '''
    BEGIN TRANSACTION;

    CREATE TABLE 'saves' (
        'save_id' INTEGER NOT NULL,

        'save_dir' TEXT NOT NULL,
        'organisation' TEXT NOT NULL,
        'seed' INTEGER NOT NULL,

        PRIMARY KEY('save_id' AUTOINCREMENT)
    );

    CREATE TABLE 'logs' (
        'log_id' INTEGER NOT NULL,

        'log_time' REAL NOT NULL,
        'save_id' INTEGER NOT NULL,

        'gameversion' TEXT DEFAULT NULL,
        'playtime' INTEGER DEFAULT NULL,
        'elapseddays' INTEGER DEFAULT NULL,
        'onlinebalance' REAL DEFAULT NULL,
        'networth' REAL DEFAULT NULL,
        'lifetimeearnings' REAL DEFAULT NULL,
        'rank' INTEGER DEFAULT NULL,
        'tier' INTEGER DEFAULT NULL,
        'xp' INTEGER DEFAULT NULL,
        'totalxp' INTEGER DEFAULT NULL,
        'discoveredproducts' INTEGER DEFAULT NULL,

        PRIMARY KEY('log_id' AUTOINCREMENT),
        FOREIGN KEY ('save_id') REFERENCES 'saves'('save_id')
    );

    COMMIT;
'''




# LIB
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def clear_display() -> None:
    if os.name == 'posix':
        subprocess.run(['/usr/bin/clear'], shell=True)
    elif os.name == 'nt':
        subprocess.run(['cls'], shell=True)
    else:
        print('\033c', end='')


def display_msg(msg: str = '', start: str = '', end: str = '\n', level: int = 0, sleep: float = 0, sleep_cd: bool = False, timestamp: bool = False, timestamp_fmt: str = '%H:%M:%S') -> None:
    if timestamp:
        msg = f"[{datetime.datetime.now().strftime(timestamp_fmt)}] {' ' * (level * 2)}{msg}"

    if sleep <= 0:
        sys.stdout.write(f'{start}{msg}{end}')
        sys.stdout.flush()
    else:
        until: float = time.time() + sleep

        while time.time() <= until:
            if not sleep_cd:
                frame: str = f"{start}{msg} "
            else:
                frame: str = f"{start}{msg} {int(until - time.time())}s "

            sys.stdout.write(frame)
            sys.stdout.flush()

            time.sleep(1)

            sys.stdout.write('\b' * len(frame))

        sys.stdout.write(end)
        sys.stdout.flush()


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




# HB
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class Hylandbook:
    Argparser: argparse.ArgumentParser
    Database: DatabaseSQLite

    args: argparse.Namespace
    save_dir: Path
    data_dir: Path
    db_file: Path

    sd_cache: dict




    def __init__(self) -> None:
        clear_display()
        display_msg(msg=BANNER, end="\n\n")

        self.Argparser = argparse.ArgumentParser(**ARGPARSER_CONF['init'])

        for v in ARGPARSER_CONF['args']:
            self.Argparser.add_argument(
                *v['name_or_flags'],
                **v['conf'],
            )

        self.args = self.Argparser.parse_args()

        if not self._init_fs():
            display_msg(msg="_init_fs failed... exiting.", start="\n")
            sys.exit(1)

        self.Database = DatabaseSQLite(file=self.db_file)

        if not self._init_db():
            display_msg(msg="_init_db failed... exiting.", start="\n")
            sys.exit(2)







    def main(self) -> None:
        con, cur = self.Database.connect()

        try:
            while True:
                clear_display()
                display_msg(msg=BANNER, end="\n\n")

                self.sd_cache = {}

                display_msg(msg=f"loading data profile ...", timestamp=True)

                sd_data: dict = {
                    # to saves
                    'save_dir': self.save_dir.name,
                    'organisation': self._sd(col='organisation'),
                    'seed': self._sd(col='seed'),
                    # to logs
                    # 'gameversion': self._sd(col='gameversion'),
                    # 'playtime': self._sd(col='playtime'),
                    # 'elapseddays': self._sd(col='elapseddays'),
                    # 'onlinebalance': self._sd(col='onlinebalance'),
                    # 'networth': self._sd(col='networth'),
                    # 'lifetimeearnings': self._sd(col='lifetimeearnings'),
                    # 'rank': self._sd(col='rank'),
                    # 'tier': self._sd(col='tier'),
                    # 'xp': self._sd(col='xp'),
                    # 'totalxp': self._sd(col='totalxp'),
                    # 'discoveredproducts': self._sd(col='discoveredproducts')
                }

                if not sd_data.get('save_dir') \
                or not sd_data.get('organisation') \
                or not sd_data.get('seed'):
                    display_msg(msg="[BOO] required sd_data values missing")
                    sys.exit(3)

                sd_id: int|None = None

                r: sqlite3.Cursor = cur.execute('''
                    SELECT save_id
                    FROM saves
                    WHERE save_dir = :save_dir AND organisation = :organisation AND seed = :seed
                    ORDER BY save_id DESC
                    LIMIT 1;
                    ''',
                    sd_data
                )

                existing_save: tuple|None = r.fetchone()

                if not existing_save:
                    # display_msg(msg="new save detected", timestamp=True)
                    r = cur.execute('''
                        INSERT INTO saves (save_dir, organisation, seed)
                        VALUES (:save_dir, :organisation, :seed);
                        ''',
                        sd_data
                    )
                    sd_id = cur.lastrowid
                    con.commit()
                else:
                    sd_id = existing_save[0]
                    # display_msg(msg=f"existing save detected, id {sd_id}", timestamp=True)

                if not sd_id:
                    display_msg(msg="[BOO] failed to get sd_id")
                    sys.exit(2)

                # display_msg(msg=f"logging as save_id {sd_id}", timestamp=True)

                display_msg(msg=f"processing save game data ...", timestamp=True)

                sd_data = {
                    **sd_data,
                    **{
                        'gameversion': self._sd(col='gameversion'),
                        'playtime': self._sd(col='playtime'),
                        'elapseddays': self._sd(col='elapseddays'),
                        'onlinebalance': self._sd(col='onlinebalance'),
                        'networth': self._sd(col='networth'),
                        'lifetimeearnings': self._sd(col='lifetimeearnings'),
                        'rank': self._sd(col='rank'),
                        'tier': self._sd(col='tier'),
                        'xp': self._sd(col='xp'),
                        'totalxp': self._sd(col='totalxp'),
                        'discoveredproducts': self._sd(col='discoveredproducts')
                    },
                }

                # print('sd_data  ', sd_data)
                # print('sd_cache ', self.sd_cache)
                # print('sd_id    ', sd_id)

                r: sqlite3.Cursor = cur.execute('''
                    SELECT gameversion, onlinebalance, networth, lifetimeearnings, rank, tier, xp, totalxp, discoveredproducts
                    FROM logs
                    WHERE save_id = :save_id
                    ORDER BY log_id DESC
                    LIMIT 1;
                    ''',
                    {'save_id': sd_id}
                )

                previous: tuple|None = r.fetchone()
                current: dict = sd_data.copy()
                del current['save_dir']
                del current['organisation']
                del current['playtime']
                del current['elapseddays']
                del current['seed']

                if previous == tuple(current.values()):
                    display_msg(msg="no changes detected", timestamp=True)
                else:
                    display_msg(msg="changes detected", timestamp=True)
                    cur.execute('''
                        INSERT INTO logs (log_time, save_id, gameversion, playtime, elapseddays, onlinebalance, networth, lifetimeearnings, rank, tier, xp, totalxp, discoveredproducts)
                        VALUES (:log_time, :save_id, :gameversion, :playtime, :elapseddays, :onlinebalance, :networth, :lifetimeearnings, :rank, :tier, :xp, :totalxp, :discoveredproducts);
                        ''',
                        dict({
                            **{
                                'log_time': time.time(),
                                'save_id': sd_id,
                            },
                            **sd_data,
                        })
                    )
                    con.commit()

                    display_msg(msg=f"logged saves.save_id {sd_id} logs.log_id {cur.lastrowid}", timestamp=True)

                display_msg(msg=json.dumps(obj=sd_data, indent=4))
                display_msg(msg=f"next check in", timestamp=True, sleep=CHECK_INTERVAL, sleep_cd=True)

        finally:
            con.close()










    def _sd(self, col: str) -> str|int|float|None:
        time.sleep(SD_THROTTLE)

        data: dict|None

        if col == 'gameversion':
            data = self._sd_data(f='Game.json') or {}
            if data.get('GameVersion'):
                return str(data['GameVersion'])

        if col == 'organisation':
            data = self._sd_data(f='Game.json') or {}
            if data.get('OrganisationName'):
                return str(data['OrganisationName'])

        if col == 'seed':
            data = self._sd_data(f='Game.json') or {}
            if data.get('Seed'):
                return int(data['Seed'])

        if col == 'playtime':
            data = self._sd_data(f='Time.json') or {}
            if data.get('Playtime'):
                return int(data['Playtime'])

        if col == 'elapseddays':
            data = self._sd_data(f='Time.json') or {}
            if data.get('ElapsedDays'):
                return int(data['ElapsedDays'])

        if col == 'onlinebalance':
            data = self._sd_data(f='Money.json') or {}
            if data.get('OnlineBalance'):
                return float(data['OnlineBalance'])

        if col == 'networth':
            data = self._sd_data(f='Money.json') or {}
            if data.get('Networth'):
                return float(data['Networth'])

        if col == 'lifetimeearnings':
            data = self._sd_data(f='Money.json') or {}
            if data.get('LifetimeEarnings'):
                return float(data['LifetimeEarnings'])

        if col == 'rank':
            data = self._sd_data(f='Rank.json') or {}
            if data.get('Rank'):
                return int(data['Rank'])

        if col == 'tier':
            data = self._sd_data(f='Rank.json') or {}
            if data.get('Tier'):
                return int(data['Tier'])

        if col == 'xp':
            data = self._sd_data(f='Rank.json') or {}
            if data.get('XP'):
                return int(data['XP'])

        if col == 'totalxp':
            data = self._sd_data(f='Rank.json') or {}
            if data.get('TotalXP'):
                return int(data['TotalXP'])

        if col == 'discoveredproducts':
            data = self._sd_data(f='Products.json') or {}
            if data.get('DiscoveredProducts'):
                if type(data['DiscoveredProducts']):
                    return len(data['DiscoveredProducts'])

        return None




    def _sd_data(self, f: str) -> dict|None:
        if self.sd_cache.get(f):
            return self.sd_cache[f]

        file = self.save_dir.joinpath(f)

        if not file.is_file():
            return None

        try:
            data: dict = json.loads(s=file.read_text())
            self.sd_cache[f] = data

        except json.JSONDecodeError as e:
            display_msg(msg=f"[BOO] loading `{f}` sd_data failed: {e}")
            return None

        if not data:
            return None

        return data




    def _init_fs(self) -> bool:
        self.save_dir = Path(self.args.save_dir).resolve()
        self.data_dir = Path(self.args.data_dir).resolve()
        self.db_file = self.data_dir.joinpath('data.db')

        if not self.save_dir.exists() or not self.save_dir.is_dir():
            display_msg(msg=f"[BOO] save_dir does not exist or is not a directory: {self.save_dir}")
            return False

        if not self.data_dir.exists() or not self.data_dir.is_dir():
            display_msg(msg=f"data_dir does not exist yet: {self.data_dir}")

            if input("create it now? [y/n]: ").strip().lower() != 'y':
                return False

            self.data_dir.mkdir()

            if not self.data_dir.exists():
                display_msg(msg=f"[BOO] could not create data_dir: {self.data_dir}")
                return False


        return True


    def _init_db(self) -> bool:
        if not self.db_file.exists():
            con, cur = self.Database.connect()
            try:
                cur.executescript(DB_SCHEMA)
            except:
                self.db_file.unlink(missing_ok=True)
                return False
            finally:
                con.close()

        return True








if __name__ == '__main__':
    try:
        App = Hylandbook()
        App.main()
    except KeyboardInterrupt:
        pass

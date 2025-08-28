'''
HYLANDBOOK

Log your Schedule I progress.
SAVEGAME_PATH is required, optional arguments will use their defaults if not set by you.
PATH for --data-dir must not exist before you start the tool, but you will be asked for confirmation before it gets created automatically.

I tested this last on game version 0.3.6f6.
'''

import argparse
import csv
import datetime
import json
import os
import sqlite3
import subprocess
import sys
import time
from pathlib import Path




# SETUP
# ==================================================================================================

BANNER: str = '-=[ H Y L A N D B O O K ]=-'
DEFAULT_DATA_DIR: Path = Path.cwd() / 'hb_data'
DB_FILE_NAME: str = 'book.db'
DEFAULT_CHECK_INTERVAL: int = 60
MIN_CHECK_INTERVAL: int = 30
SD_FILE_READ_THROTTLE: float = 0
ARGPARSER_CONF: dict = {
    'init': {
        'prog': "hylandbook",
        'description': __doc__[11:] if __doc__ else '',
        'epilog': "Cool links: https://scheduleonegame.com, https://github.com/etrusci-org/hylandbook",
    },
    'args': [
        {
            'name_or_flags': ['save_dir'],
            'conf': {
                'metavar': 'SAVEGAME_PATH',
                'type': str,
                'default': None,
                'help': "path to a Schedule I 'SaveGame_*' directory, enclose it in quotes if it contains spaces, e.g. \"C:\\path to\\SaveGame_1\""
            },
        },
        {
            'name_or_flags': ['-d', '--data-dir'],
            'conf': {
                'metavar': 'PATH',
                'type': str,
                'default': DEFAULT_DATA_DIR,
                'help': f"path to directory where the logged data will be stored, default: {DEFAULT_DATA_DIR}",
            },
        },
        {
            'name_or_flags': ['-i', '--check-interval'],
            'conf': {
                'metavar': 'SECONDS',
                'type': int,
                'default': DEFAULT_CHECK_INTERVAL,
                'help': f"how frequently to check the save data for changes, in seconds, default: {DEFAULT_CHECK_INTERVAL}, minimum: {MIN_CHECK_INTERVAL}",
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
TXT_EXPORT_TPL: str = '''
           SAVE_DIR: {save_dir}
               SEED: {seed}
       GAME VERSION: {gameversion}

       ORGANISATION: {organisation}

           PLAYTIME: {playtime}
       ELAPSED DAYS: {elapseddays}

     ONLINE BALANCE: {onlinebalance}
           NETWORTH: {networth}
  LIFETIME EARNINGS: {lifetimeearnings}

               RANK: {rank}
               TIER: {tier}
                 XP: {xp}
           TOTAL XP: {totalxp}

DISCOVERED PRODUCTS: {discoveredproducts}

      (export time): {_t}
'''
HTML_EXPORT_TPL: str = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="refresh" content="60">

    <style>
        body {
            font-family: sans-serif;
            font-size: 16px;
        }
    </style>

    <title>My Schedule I Progress</title>
</head>
<body>
    <h1>My Schedule I Progress</h1>

    <pre>
             SAVE_DIR: {save_dir}
                 SEED: {seed}
         GAME VERSION: {gameversion}

         ORGANISATION: {organisation}

             PLAYTIME: {playtime}
         ELAPSED DAYS: {elapseddays}

       ONLINE BALANCE: {onlinebalance}
             NETWORTH: {networth}
    LIFETIME EARNINGS: {lifetimeearnings}

                 RANK: {rank}
                 TIER: {tier}
                   XP: {xp}
             TOTAL XP: {totalxp}

  DISCOVERED PRODUCTS: {discoveredproducts}

        (export time): {_t}
    </pre>

</body>
</html>
'''




# LIB
# ==================================================================================================

def clear_display() -> None:
    if os.name == 'posix':
        subprocess.run(['/usr/bin/clear'], shell=True)
    elif os.name == 'nt':
        subprocess.run(['cls'], shell=True)
    else:
        print('\033c', end='')


def display_msg(msg: str = '', start: str = '', end: str = "\n", level: int = 0, sleep: float = 0, sleep_cd: bool = False, timestamp: bool = False, timestamp_fmt: str = '%H:%M:%S.%f') -> None:
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




# CORE
# ==================================================================================================

class Hylandbook:
    Argparser: argparse.ArgumentParser
    Database: DatabaseSQLite
    args: argparse.Namespace
    save_dir: Path
    data_dir: Path
    db_file: Path
    sd_cache: dict = {}


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

        self.args.check_interval = max(MIN_CHECK_INTERVAL, self.args.check_interval)

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
            display_msg(msg="loading save data profile", timestamp=True)

            sd_profile: dict = {
                'save_dir': str(self.save_dir),
                'organisation': self._sd(col='organisation'),
                'seed': self._sd(col='seed'),
            }

            if not sd_profile.get('save_dir') or not sd_profile.get('organisation') or not sd_profile.get('seed'):
                display_msg(msg="[BOO] required data_profile values missing")
                sys.exit(3)

            sd_id: int|None = None
            r: sqlite3.Cursor

            r = cur.execute(
                '''
                SELECT save_id
                FROM saves
                WHERE save_dir = :save_dir AND organisation = :organisation AND seed = :seed
                ORDER BY save_id DESC
                LIMIT 1;
                ''',
                sd_profile
            )

            existing_save: tuple|None = r.fetchone()

            if not existing_save:
                r = cur.execute(
                    '''
                    INSERT INTO saves (save_dir, organisation, seed)
                    VALUES (:save_dir, :organisation, :seed);
                    ''',
                    sd_profile
                )
                sd_id = cur.lastrowid
                con.commit()
                display_msg(msg=f"new save data profile created", timestamp=True)
            else:
                sd_id = existing_save[0]
                display_msg(msg=f"existing save detected", timestamp=True)

            if not sd_id:
                display_msg(msg="[BOO] failed to get sd_id")
                sys.exit(2)

            display_msg(msg=f"  save directory: {self.save_dir}", start="\n")
            display_msg(msg=f"  data directory: {self.data_dir}")
            display_msg(msg=f"         save id: {sd_id}")
            display_msg(msg=f"    organisation: {sd_profile.get('organisation')}")
            display_msg(msg=f"            seed: {sd_profile.get('seed')}", end="\n\n")

            display_msg("to stop hylandbook once it is running, type CTRL+C or close this window", end="\n\n")

            if input("start monitoring? [y/n]: ").strip().lower() != 'y':
                return

            while True:
                clear_display()
                display_msg(msg=BANNER, end="\n\n")
                display_msg(msg="parsing save game data", timestamp=True)

                self.sd_cache = {}

                sd_log: dict = {
                    'gameversion': self._sd(col='gameversion'),
                    'playtime': self._sd(col='playtime') or 0,
                    'elapseddays': self._sd(col='elapseddays') or 0,
                    'onlinebalance': self._sd(col='onlinebalance') or 0,
                    'networth': self._sd(col='networth') or 0,
                    'lifetimeearnings': self._sd(col='lifetimeearnings') or 0,
                    'rank': self._sd(col='rank') or 0,
                    'tier': self._sd(col='tier') or 0,
                    'xp': self._sd(col='xp') or 0,
                    'totalxp': self._sd(col='totalxp') or 0,
                    'discoveredproducts': self._sd(col='discoveredproducts') or 0,
                }

                r: sqlite3.Cursor = cur.execute(
                    '''
                    SELECT onlinebalance, networth, lifetimeearnings, rank, tier, xp, totalxp, discoveredproducts
                    FROM logs
                    WHERE save_id = :save_id
                    ORDER BY log_id DESC
                    LIMIT 1;
                    ''',
                    {'save_id': sd_id}
                )

                previous: tuple|None = r.fetchone()
                current: dict = sd_log.copy()
                del current['gameversion']
                del current['playtime']
                del current['elapseddays']

                if previous == tuple(current.values()):
                    display_msg(msg="no changes detected", timestamp=True)
                else:
                    display_msg(msg="changes detected", timestamp=True)
                    cur.execute(
                        '''
                        INSERT INTO logs (log_time, save_id, gameversion, playtime, elapseddays, onlinebalance, networth, lifetimeearnings, rank, tier, xp, totalxp, discoveredproducts)
                        VALUES (:log_time, :save_id, :gameversion, :playtime, :elapseddays, :onlinebalance, :networth, :lifetimeearnings, :rank, :tier, :xp, :totalxp, :discoveredproducts);
                        ''',
                        {
                            **{
                                'log_time': time.time(),
                                'save_id': sd_id,
                            },
                            **sd_log,
                        }
                    )
                    con.commit()
                    # display_msg(msg=f"logged saves.save_id {sd_id} logs.log_id {cur.lastrowid}", timestamp=True)
                self._export(current_profile_data=sd_profile, current_log_data=sd_log, save_id=sd_id)

                display_msg()
                for k, v in sd_log.items():
                    display_msg(f"{k:>20}: {v}")
                display_msg()

                display_msg(msg="next check in", sleep=self.args.check_interval, sleep_cd=True)

        finally:
            con.close()


    def _sd(self, col: str) -> str|int|float|None:
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

        time.sleep(SD_FILE_READ_THROTTLE)

        try:
            data: dict = json.loads(s=file.read_text())
            self.sd_cache[f] = data

        except json.JSONDecodeError as e:
            display_msg(msg=f"[BOO] failed to load `{f}`: {e}")
            return None

        if not data:
            return None

        return data


    def _init_fs(self) -> bool:
        self.save_dir = Path(self.args.save_dir).resolve()
        self.data_dir = Path(self.args.data_dir).resolve()
        self.db_file = self.data_dir.joinpath(DB_FILE_NAME)

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


        # raise Exception('test ing')

        return True


    def _export(self, current_profile_data: dict, current_log_data: dict, save_id: int) -> None:
        # display_msg(msg=f"exporting data", timestamp=True)

        # prep current data
        current: dict = {
            'save': current_profile_data.copy(),
            'log': current_log_data.copy(),
        }
        current['save']['save_dir'] = Path(current['save']['save_dir']).name
        tpl_values: dict = {
            **current['save'],
            **current['log'],
            '_t': datetime.datetime.now().strftime('%H:%M:%S'),
        }

        # current json
        file: Path = self.data_dir.joinpath('current.json')
        file.write_text(data=json.dumps(obj=current, indent=4))

        # current txt
        file: Path = self.data_dir.joinpath('current.txt')
        tpl_file: Path = self.data_dir.joinpath('current.txt.tpl')
        if not tpl_file.exists():
            tpl_file.write_text(data=TXT_EXPORT_TPL.strip('\n'))
        content: str = tpl_file.read_text()
        for k, v in tpl_values.items():
            content = content.replace(f'{{{k}}}', str(v))
        file.write_text(data=content)

        # current html
        file: Path = self.data_dir.joinpath('current.html')
        tpl_file: Path = self.data_dir.joinpath('current.html.tpl')
        if not tpl_file.exists():
            tpl_file.write_text(data=HTML_EXPORT_TPL.strip('\n'))
        content: str = tpl_file.read_text()
        for k, v in tpl_values.items():
            content = content.replace(f'{{{k}}}', str(v))
        file.write_text(data=content)

        # prep history data
        con, cur = self.Database.connect()
        try:
            r: sqlite3.Cursor = cur.execute('SELECT * FROM logs WHERE save_id = :save_id', {'save_id': save_id})
            history_rows: list = r.fetchall()
            history_cols: list = [v[0] for v in cur.description]
        finally:
            con.close()

        history: dict = {
            'save': current_profile_data.copy(),
            'log': [dict(zip(history_cols, row)) for row in history_rows],
        }
        history['save']['save_dir'] = Path(history['save']['save_dir']).name

        # history json
        file: Path = self.data_dir.joinpath(f'history-{save_id}.json')
        file.write_text(data=json.dumps(obj=history, indent=4))

        # history csv
        # does not contain data profile
        file: Path = self.data_dir.joinpath(f'history-{save_id}.csv')
        with open(file=file, mode='w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(history_cols)
            writer.writerows(history_rows)




# RUN
# ==================================================================================================

if __name__ == '__main__':
    try:
        App = Hylandbook()
        App.main()
    except Exception as e:
        print(f"\n[BOO] {e}")
        input("press any key to exit")
    except KeyboardInterrupt:
        print("\nexiting")

import datetime
import json
import sqlite3
import sys
import time
from pathlib import Path

import hylandbook.argparser
import hylandbook.database
from hylandbook import conf
from hylandbook import display




class HylandbookExporter:
    Database: hylandbook.database.DatabaseSQLite
    data_dir: Path
    sd_id: int | None = None


    def __init__(self, db: hylandbook.database.DatabaseSQLite, data_dir: Path) -> None:
        self.Database = db


    def update_exports(self, sd_id: int | None) -> None:
        if not sd_id:
            return

        con, cur = self.Database.connect()

        try:
            print('update_current', sd_id)
            print('update_history', sd_id)

        finally:
            con.close()




class Hylandbook:
    Database: hylandbook.database.DatabaseSQLite
    Exporter: HylandbookExporter

    args: dict

    save_dir: Path
    data_dir: Path
    db_file: Path

    sd_cache: dict = {}
    sd_current: dict = {}
    sd_id: int | None = None
    sd_org: str = ''


    def __init__(self) -> None:
        # display.clear()
        # display.msg(conf.APP_BANNER)

        self.args = hylandbook.argparser.Argparser(conf=conf.ARGPARSER).parse()
        self.args['check_interval'] = max(conf.MIN_CHECK_INTERVAL, self.args['check_interval'])

        if not self._init_fs():
            display.msg("_init_fs failed", start="\n")
            input("\npress [Enter] to exit")
            sys.exit(1)

        self.Database = hylandbook.database.DatabaseSQLite(file=self.db_file)

        if not self._init_db():
            display.msg("_init_db failed", start="\n")
            input("\npress [Enter] to exit")
            sys.exit(2)

        self.Exporter = HylandbookExporter(db=self.Database, data_dir=self.data_dir)


    def main(self) -> None:
        display.clear()
        display.msg(conf.APP_BANNER)

        if not self._init_sd_profile():
            display.msg("[BOO] failed to initialize sd_profile")
            return

        self._log_sd_changes()


    def _init_fs(self) -> bool:
        self.save_dir = Path(self.args['save_dir']).resolve()
        self.data_dir = Path(self.args['data_dir']).resolve()
        self.db_file = self.data_dir.joinpath(conf.DATABASE_FILE_NAME)

        if not self.save_dir.exists() or not self.save_dir.is_dir():
            display.msg(f"[BOO] save_dir does not exist or is not a directory: {self.save_dir}")
            return False

        if not self.data_dir.exists():
            display.msg(f"data_dir does not exist yet: {self.data_dir}")

            if input("create it now? [y/n]: ").strip().lower() != 'y':
                return False

            self.data_dir.mkdir()

            if not self.data_dir.exists():
                display.msg(f"[BOO] could not create data_dir: {self.data_dir}")
                return False

        return True


    def _init_db(self) -> bool:
        if not self.db_file.exists():
            con, cur = self.Database.connect()

            try:
                cur.executescript(conf.DATABASE_SCHEMA)
            except:
                self.db_file.unlink(missing_ok=True)
                return False
            finally:
                con.close()

        return True


    def _sd(self, col: str) -> str | int | float | None:
        data: dict | None

        if col == 'organisation':
            data = self._sd_data(f='Game.json')
            if data.get('OrganisationName'):
                return str(data['OrganisationName'])

        if col == 'seed':
            data = self._sd_data(f='Game.json')
            if data.get('Seed'):
                return int(data['Seed'])

        if col == 'gameversion':
            data = self._sd_data(f='Game.json')
            if data.get('GameVersion'):
                return str(data['GameVersion'])

        if col == 'playtime':
            data = self._sd_data(f='Time.json')
            if data.get('Playtime'):
                return int(data['Playtime'])

        if col == 'elapseddays':
            data = self._sd_data(f='Time.json')
            if data.get('ElapsedDays'):
                return int(data['ElapsedDays'])

        if col == 'onlinebalance':
            data = self._sd_data(f='Money.json')
            if data.get('OnlineBalance'):
                return float(data['OnlineBalance'])

        if col == 'networth':
            data = self._sd_data(f='Money.json')
            if data.get('Networth'):
                return float(data['Networth'])

        if col == 'lifetimeearnings':
            data = self._sd_data(f='Money.json')
            if data.get('LifetimeEarnings'):
                return float(data['LifetimeEarnings'])

        if col == 'rank':
            data = self._sd_data(f='Rank.json')
            if data.get('Rank'):
                return int(data['Rank'])

        if col == 'tier':
            data = self._sd_data(f='Rank.json')
            if data.get('Tier'):
                return int(data['Tier'])

        if col == 'xp':
            data = self._sd_data(f='Rank.json')
            if data.get('XP'):
                return int(data['XP'])

        if col == 'totalxp':
            data = self._sd_data(f='Rank.json')
            if data.get('TotalXP'):
                return int(data['TotalXP'])

        if col == 'discoveredproducts':
            data = self._sd_data(f='Products.json')
            if data.get('DiscoveredProducts'):
                return len(data['DiscoveredProducts'])

        # New! OwnedVehicles
        if col == 'ownedvehicles':
            data = self._sd_data(f='OwnedVehicles.json')
            if data.get('Vehicles'):
                return len(data['Vehicles'])

        return None


    def _sd_data(self, f: str) -> dict:
        if self.sd_cache.get(f):
            return self.sd_cache[f]

        file: Path = self.save_dir.joinpath(f)

        if not file.is_file():
            return {}

        if conf.SD_FILE_READ_THROTTLE > 0:
            time.sleep(conf.SD_FILE_READ_THROTTLE)

        try:
            data: dict = json.loads(s=file.read_text())
            self.sd_cache[f] = data
        except json.JSONDecodeError as e:
            display.msg(f"[BOO] failed to load `{f}`: {e}")
            return {}

        if not data:
            return {}

        return data


    def _init_sd_profile(self) -> bool:
        con, cur = self.Database.connect()

        try:
            display.msg("loading save data profile", ts=True)

            sd_profile: dict = {
                'save_dir': str(self.save_dir.name),
                'organisation': self._sd(col='organisation'),
                'seed': self._sd(col='seed'),
            }

            if not sd_profile.get('save_dir') \
               or not sd_profile.get('organisation') \
               or not sd_profile.get('seed'):
                display.msg("[BOO] required data_profile values missing")
                return False

            dump: sqlite3.Cursor

            dump = cur.execute(
                '''
                SELECT save_id
                FROM saves
                WHERE
                    save_dir = :save_dir
                    AND organisation = :organisation
                    AND seed = :seed
                ORDER BY save_id DESC
                LIMIT 1;
                ''',
                sd_profile
            )

            existing_save: tuple | None = dump.fetchone()

            if not existing_save:
                dump = cur.execute(
                    '''
                    INSERT INTO saves (save_dir, organisation, seed)
                    VALUES (:save_dir, :organisation, :seed);
                    ''',
                    sd_profile
                )
                con.commit()

                self.sd_id = cur.lastrowid
                display.msg("new save data profile created", ts=True)
            else:
                self.sd_id = existing_save[0]
                display.msg("existing save detected", ts=True)

            if not self.sd_id:
                display.msg("[BOO] failed to get sd_id")
                return False

            self.sd_org = sd_profile['organisation']

            display.msg(f"    save directory: {self.save_dir}", start="\n")
            display.msg(f"    data directory: {self.data_dir}")
            display.msg(f"           save id: {self.sd_id}")
            display.msg(f"      organisation: {self.sd_org}")
            display.msg(f"              seed: {sd_profile['seed']}", end="\n\n")

            display.msg("to quit this tool while it is running, type CTRL+C or close this window", end="\n\n")

            if input("start monitoring? [y/n]: ").strip().lower() != 'y':
                return False

            return True

        finally:
            con.close()


    def _log_sd_changes(self) -> None:
        if not self.sd_id:
            display.msg("[BOO] missing sd_id")
            return

        con, cur = self.Database.connect()

        try:
            while True:
                display.clear()
                display.msg(conf.APP_BANNER)

                display.msg("parsing save game data ...", ts=True)

                self.sd_cache = {}

                sd_log: dict = {
                    'gameversion': self._sd(col='gameversion') or '',
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
                    'ownedvehicles': self._sd(col='ownedvehicles') or 0,
                }

                dump: sqlite3.Cursor = cur.execute(
                    '''
                    SELECT elapseddays, onlinebalance, networth, lifetimeearnings, rank, tier, xp, totalxp, discoveredproducts, ownedvehicles
                    FROM logs
                    WHERE save_id = :save_id
                    ORDER BY log_id DESC
                    LIMIT 1;
                    ''',
                    {'save_id': self.sd_id}
                )

                previous: tuple | None = dump.fetchone()
                current: dict = sd_log.copy()
                del current['gameversion']
                del current['playtime']

                if previous == tuple(current.values()):
                    display.msg("no changes detected", ts=True)
                else:
                    display.msg("changes detected", ts=True)

                    cur.execute(
                        '''
                        INSERT INTO logs (log_time, save_id, gameversion, playtime, elapseddays, onlinebalance, networth, lifetimeearnings, rank, tier, xp, totalxp, discoveredproducts, ownedvehicles)
                        VALUES (:log_time, :save_id, :gameversion, :playtime, :elapseddays, :onlinebalance, :networth, :lifetimeearnings, :rank, :tier, :xp, :totalxp, :discoveredproducts, :ownedvehicles);
                        ''',
                        {
                            **{
                                'log_time': time.time(),
                                'save_id': self.sd_id,
                            },
                            **sd_log,
                        }
                    )
                    con.commit()

                self.Exporter.update_exports(sd_id=self.sd_id)

                display.msg()
                summary_indent: int = max([len(k) for k in sd_log]) + 4
                display.msg(f"{'organisation':>{summary_indent}}: {self.sd_org}")
                for k, v in sd_log.items():
                    display.msg(f"{k:>{summary_indent}}: {v}")

                display.msg(f"next check at {datetime.datetime.fromtimestamp(time.time() + self.args['check_interval']).strftime('%H:%M:%S')} ...", start="\n")
                time.sleep(self.args['check_interval'])
        finally:
            con.close()

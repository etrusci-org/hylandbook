import json
import sqlite3
import sys
import time
from pathlib import Path

import hylandbook.argparser
import hylandbook.database
import hylandbook.conf
import hylandbook.screen




Conf = hylandbook.conf.Conf()
Screen = hylandbook.screen.Screen()




class App:
    Argparser: hylandbook.argparser.Argparser
    Database: hylandbook.database.DatabaseSQLite

    args: dict

    save_dir: Path
    data_dir: Path
    db_file: Path

    sd_profile: dict = {}
    sd_log: dict = {}
    sd_cache: dict = {}


    def __init__(self) -> None:
        self.Argparser = hylandbook.argparser.Argparser(conf=Conf.argparser)


    def main(self) -> None:
        Screen.clear()
        Screen.msg(Conf.app_banner, end="\n\n")

        if len(sys.argv) < 2:
            self.Argparser.help()
            Screen.prompt_to_exit()

        self.args = self.Argparser.parse()
        self.args['check_interval'] = max(Conf.min_check_interval, self.args['check_interval'])
        print(self.args)

        if not self._init_fs():
            return

        if not self._init_db():
            return

        if not self._init_sd_profile():
            return

        Screen.msg(f" save game data directory: {self.save_dir}", start="\n")
        Screen.msg(f"{Conf.app_name} data directory: {self.data_dir}")
        Screen.msg(f"             organisation: {self.sd_profile['organisation']}", end="\n\n")

        Screen.msg("to quit at any time, type [CTRL]+[C] or close this window", end="\n\n")

        if input("start monitoring? [y/n]: ").strip().lower() != 'y':
            return

        self._monitor_sd()


    def _init_fs(self) -> bool:
        self.save_dir = Path(self.args['save_dir']).resolve()
        self.data_dir = Path(self.args['data_dir']).resolve()
        self.db_file = self.data_dir.joinpath(Conf.db_file_name)

        if not self.save_dir.exists() or not self.save_dir.is_dir():
            Screen.msg(f"save_dir does not exist or is not a directory: {self.save_dir}")
            return False

        if not self.data_dir.exists():
            # Screen.msg(f"data_dir does not exist yet: {self.data_dir}")
            # if input("create it now? [y/n]: ").strip().lower() != 'y':
            #     return False
            self.data_dir.mkdir()

            if not self.data_dir.exists():
                Screen.msg(f"[BOO] failed to create data_dir: {self.data_dir}")
                return False

        return True


    def _init_db(self) -> bool:
        self.Database = hylandbook.database.DatabaseSQLite(file=self.db_file)

        if not self.db_file.exists():
            con, cur = self.Database.connect()
            try:
                cur.executescript(Conf.db_schema)
            except sqlite3.OperationalError as e:
                Screen.msg(f"[BOO] failed to create database file: {e}")
                con.close()
                self.db_file.unlink(missing_ok=True)
                return False
            finally:
                con.close()

        return True


    def _init_sd_profile(self) -> bool:
        Screen.msg("loading save data profile ...")

        con, cur = self.Database.connect()

        try:
            self.sd_profile['save_dir'] = self.save_dir.name
            self.sd_profile['organisation'] = self._sd('organisation')
            self.sd_profile['seed'] = self._sd('seed')

            if not self.sd_profile.get('save_dir'):
                Screen.msg("[BOO] missing profile value 'save_dir'")
                return False

            if not self.sd_profile.get('organisation'):
                Screen.msg("[BOO] missing profile value 'organisation'")
                return False

            if not self.sd_profile.get('seed'):
                Screen.msg("[BOO] missing profile value 'seed'")
                return False

            r: sqlite3.Cursor = cur.execute(
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
                self.sd_profile
            )

            existing_profile: sqlite3.Row | None = r.fetchone()

            if not existing_profile:
                cur.execute(
                    '''
                    INSERT INTO saves (save_dir, organisation, seed)
                    VALUES (:save_dir, :organisation, :seed);
                    ''',
                    self.sd_profile
                )
                con.commit()
                self.sd_profile['save_id'] = cur.lastrowid
                Screen.msg("new save profile created")
            else:
                self.sd_profile['save_id'] = existing_profile['save_id']
                Screen.msg("existing save profile found")

            if not self.sd_profile.get('save_id'):
                Screen.msg("[BOO] failed to get save_id")
                return False

            # Screen.msg(f"save profile loaded")
        finally:
            con.close()

        return True


    def _monitor_sd(self) -> None:
        con, cur = self.Database.connect()

        try:
            while True:
                Screen.clear()
                Screen.msg(Conf.app_banner, end="\n\n")

                Screen.msg("parsing save game data ...", ts=True)

                self.sd_cache = {}

                self.sd_log['gameversion'] = self._sd('gameversion')  # do not use for comparsion
                self.sd_log['playtime'] = self._sd('playtime')  # do not use for comparsion
                self.sd_log['elapseddays'] = self._sd('elapseddays')
                self.sd_log['onlinebalance'] = self._sd('onlinebalance')
                self.sd_log['networth'] = self._sd('networth')
                self.sd_log['lifetimeearnings'] = self._sd('lifetimeearnings')
                self.sd_log['rank'] = self._sd('rank')
                self.sd_log['tier'] = self._sd('tier')
                self.sd_log['xp'] = self._sd('xp')
                self.sd_log['totalxp'] = self._sd('totalxp')
                self.sd_log['discoveredproducts'] = self._sd('discoveredproducts')
                self.sd_log['ownedvehicles'] = self._sd('ownedvehicles')

                r: sqlite3.Cursor = cur.execute(
                    '''
                    SELECT elapseddays, onlinebalance, networth, lifetimeearnings, rank, tier, xp, totalxp, discoveredproducts, ownedvehicles
                    FROM logs
                    WHERE save_id = :save_id
                    ORDER BY log_id DESC
                    LIMIT 1;
                    ''',
                    self.sd_profile
                )

                dump: sqlite3.Row | None = r.fetchone()

                previous: dict = dict(dump) if dump else {}
                current: dict = self.sd_log.copy()
                del current['gameversion']
                del current['playtime']

                if dict(previous or {}) == current:
                    Screen.msg("no changes detected", ts=True)
                else:
                    Screen.msg("changes detected", ts=True)
                    cur.execute(
                        '''
                        INSERT INTO logs (log_time, save_id, gameversion, playtime, elapseddays, onlinebalance, networth, lifetimeearnings, rank, tier, xp, totalxp, discoveredproducts, ownedvehicles)
                        VALUES (:log_time, :save_id, :gameversion, :playtime, :elapseddays, :onlinebalance, :networth, :lifetimeearnings, :rank, :tier, :xp, :totalxp, :discoveredproducts, :ownedvehicles);
                        ''',
                        {
                            'log_time': time.time(),
                            **self.sd_profile,
                            **self.sd_log,
                        }
                    )
                    con.commit()

                    self._export()

                Screen.msg()
                self._print_monitor_summary(previous=previous, current=current)
                Screen.msg()

                Screen.msg("next check in", sleep=self.args['check_interval'])
        finally:
            con.close()


    def _print_monitor_summary(self, previous: dict, current: dict):
        indent: int = max([len(k) for k in current])

        Screen.msg(f"{'organisation':>{indent}}  {self.sd_profile['organisation']}")
        for k, v in current.items():
            Screen.msg(f"{k:>{indent}}", end='  ')
            if k in previous.keys() and previous.get(k) != v:
                Screen.msg(f"{previous[k]} -> {v}")
            else:
                Screen.msg(f"{v}")


    def _sd(self, col: str, /) -> str | int | float | None:
        default_organisation: str = ''
        default_seed: int = 0
        default_gameversion: str = ''
        default_playtime: int = 0
        default_elapseddays: int = 0
        default_onlinebalance: float = 0
        default_networth: float = 0
        default_lifetimeearnings: float = 0
        default_rank: int = 0
        default_tier: int = 0
        default_xp: int = 0
        default_totalxp: int = 0
        default_discoveredproducts: int = 0
        default_ownedvehicles: int = 0

        data: dict = {}

        if col == 'organisation':
            data = self._sd_data('Game.json')
            if not data.get('OrganisationName'):
                return default_organisation
            return str(data['OrganisationName'])

        if col == 'seed':
            data = self._sd_data('Game.json')
            if not data.get('Seed'):
                return default_seed
            return int(data['Seed'])

        if col == 'gameversion':
            data = self._sd_data('Game.json')
            if not data.get('GameVersion'):
                return default_gameversion
            return str(data['GameVersion'])

        if col == 'playtime':
            data = self._sd_data('Time.json')
            if not data.get('Playtime'):
                return default_playtime
            return int(data['Playtime'])

        if col == 'elapseddays':
            data = self._sd_data('Time.json')
            if not data.get('ElapsedDays'):
                return default_elapseddays
            return int(data['ElapsedDays'])

        if col == 'onlinebalance':
            data = self._sd_data('Money.json')
            if not data.get('OnlineBalance'):
                return default_onlinebalance
            return float(data['OnlineBalance'])

        if col == 'networth':
            data = self._sd_data('Money.json')
            if not data.get('Networth'):
                return default_networth
            return float(data['Networth'])

        if col == 'lifetimeearnings':
            data = self._sd_data('Money.json')
            if not data.get('LifetimeEarnings'):
                return default_lifetimeearnings
            return float(data['LifetimeEarnings'])

        if col == 'rank':
            data = self._sd_data('Rank.json')
            if not data.get('Rank'):
                return default_rank
            return int(data['Rank'])

        if col == 'tier':
            data = self._sd_data('Rank.json')
            if not data.get('Tier'):
                return default_tier
            return int(data['Tier'])

        if col == 'xp':
            data = self._sd_data('Rank.json')
            if not data.get('XP'):
                return default_xp
            return int(data['XP'])

        if col == 'totalxp':
            data = self._sd_data('Rank.json')
            if not data.get('TotalXP'):
                return default_totalxp
            return int(data['TotalXP'])

        if col == 'discoveredproducts':
            data = self._sd_data('Products.json')
            if not data.get('DiscoveredProducts'):
                return default_discoveredproducts
            return len(data['DiscoveredProducts'])

        if col == 'ownedvehicles':
            data = self._sd_data('OwnedVehicles.json')
            if not data.get('Vehicles'):
                return default_ownedvehicles
            return len(data['Vehicles'])

        return None


    def _sd_data(self, sd_file: str, /) -> dict:
        if self.sd_cache.get(sd_file):
            return self.sd_cache[sd_file]

        file: Path = self.save_dir.joinpath(sd_file)

        if not file.is_file():
            return {}

        if Conf.sd_file_read_throttle > 0:
            time.sleep(Conf.sd_file_read_throttle)

        try:
            data: dict = json.loads(s=file.read_text())
            self.sd_cache[sd_file] = data
        except json.JSONDecodeError as e:
            Screen.msg(f"[BOO] failed to load '{sd_file}': {e}")
            return {}

        if not data:
            return {}

        return data


    def _export(self, keys: list[str] = ['all']) -> None:
        if 'disabled' in self.args['export_types']:
            return

        current_data: dict = {
            '_t': time.time(),
            **self.sd_profile,
            **self.sd_log,
        }

        file: Path | None = None
        data: str | None = None

        for t in self.args['export_types']:
            if t == 'json':
                file = self.data_dir.joinpath('current.json')
                if 'all' in self.args['export_keys']:
                    data = json.dumps(obj=current_data, indent=4)
                else:
                    dump: dict = {}
                    for k in self.args['export_keys']:
                        if current_data.get(k):
                            dump[k] = current_data[k]
                    data = json.dumps(obj=dump, indent=4)

            if t == 'txt':
                file = self.data_dir.joinpath('current.txt')
                indent: int = 0
                if 'all' in self.args['export_keys']:
                    indent = max([len(k) for k in current_data])
                    data = '\n'.join([f"{k:>{indent}}  {v}" for k, v in current_data.items()])
                else:
                    dump: dict = {}
                    for k in self.args['export_keys']:
                        if current_data.get(k):
                            dump[k] = current_data[k]
                    indent = max([len(k) for k in dump])
                    data = '\n'.join([f"{k:>{indent}}  {v}" for k, v in dump.items()])

            if file and data:
                file.write_text(data)





        # # history test
        # con, cur = self.Database.connect()
        # try:
        #     r: sqlite3.Cursor = cur.execute(
        #         '''
        #         SELECT *
        #         FROM logs
        #         WHERE save_id = :save_id
        #         ORDER BY log_id DESC
        #         LIMIT 100;
        #         ''',
        #         self.sd_profile
        #     )
        #     dump: list[sqlite3.Row] | None = r.fetchall()
        #     for row in dump:
        #         print(type(row), dict(row))
        # finally:
        #     con.close()

import csv
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
    current_json_export_file: Path
    current_txt_export_file: Path
    history_json_export_file: Path
    history_csv_export_file: Path

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
            Screen.prompt_to_exit(0)

        self.args = self.Argparser.parse()
        self.args['check_interval'] = max(Conf.min_check_interval, self.args['check_interval'])
        self.args['history_limit'] = max(Conf.min_history_limit, self.args['history_limit']) if self.args['history_limit'] else None

        if not self._init_fs():
            Screen.prompt_to_exit(1)
            return

        if not self._init_db():
            Screen.prompt_to_exit(2)
            return

        if not self._init_sd_profile():
            Screen.prompt_to_exit(3)
            return

        Screen.msg(f"   save folder  {self.save_dir}", start="\n")
        Screen.msg(f"   data folder  {self.data_dir}")
        Screen.msg(f"  organisation  {self.sd_profile['organisation']}", end="\n\n")

        Screen.msg("to quit at any time, type [CTRL]+[C] or close this window", end="\n\n")

        if input("start monitoring? [y/n]: ").strip().lower() != 'y':
            return

        self._monitor_sd()


    def _init_fs(self) -> bool:
        self.save_dir = Path(self.args['save_dir']).resolve()
        self.data_dir = Path(self.args['data_dir']).resolve()
        self.db_file = self.data_dir.joinpath(Conf.db_file_name)
        self.current_json_export_file = self.data_dir.joinpath(Conf.current_json_export_file_name)
        self.current_txt_export_file = self.data_dir.joinpath(Conf.current_txt_export_file_name)
        self.history_json_export_file = self.data_dir.joinpath(Conf.history_json_export_file_name)
        self.history_csv_export_file = self.data_dir.joinpath(Conf.history_csv_export_file_name)

        if not self.save_dir.exists() or not self.save_dir.is_dir():
            Screen.msg(f"[BOO] SAVEGAME_PATH does not exist or is not a folder: {self.save_dir}")
            return False

        if not self.data_dir.exists():
            self.data_dir.mkdir()

            if not self.data_dir.exists():
                Screen.msg(f"[BOO] failed to create data folder: {self.data_dir}")
                return False

        dummy_time: float = time.time()
        dummy_msg: str = 'no data logged yet'

        if 'json' in self.args['export_current'] and not self.current_json_export_file.exists():
            self.current_json_export_file.write_text(data=f'{{"_t": {dummy_time}, "msg": "{dummy_msg}"}}')

        if 'txt' in self.args['export_current'] and not self.current_txt_export_file.exists():
            self.current_txt_export_file.write_text(data=f' _t  {dummy_time}\nmsg  {dummy_msg}')

        if 'json' in self.args['export_history'] and not self.history_json_export_file.exists():
            self.history_json_export_file.write_text(data=f'[{{"_t": {dummy_time}, "msg": "{dummy_msg}"}}]')

        if 'csv' in self.args['export_history'] and not self.history_csv_export_file.exists():
            self.history_csv_export_file.write_text(data=f'_t,msg\n{dummy_time},"{dummy_msg}"')

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
        finally:
            con.close()

        return True


    def _monitor_sd(self) -> None:
        while True:
            con, cur = self.Database.connect()

            try:
                Screen.clear()
                Screen.msg(Conf.app_banner, end="\n\n")

                Screen.msg("reading save game data ...", ts=True)

                self.sd_cache = {}

                self.sd_log['gameversion'] = self._sd('gameversion')  # do not use for comparsion
                self.sd_log['playtime'] = self._sd('playtime')  # do not use for comparsion
                self.sd_log['timeofday'] = self._sd('timeofday')  # do not use for comparsion
                self.sd_log['elapseddays'] = self._sd('elapseddays')
                self.sd_log['cashbalance'] = self._sd('cashbalance')
                self.sd_log['onlinebalance'] = self._sd('onlinebalance')
                self.sd_log['networth'] = self._sd('networth')
                self.sd_log['lifetimeearnings'] = self._sd('lifetimeearnings')
                self.sd_log['rank'] = self._sd('rank')
                self.sd_log['tier'] = self._sd('tier')
                self.sd_log['xp'] = self._sd('xp')
                self.sd_log['totalxp'] = self._sd('totalxp')
                self.sd_log['discoveredproducts'] = self._sd('discoveredproducts')
                self.sd_log['ownedbusinesses'] = self._sd('ownedbusinesses')
                self.sd_log['ownedproperties'] = self._sd('ownedproperties')
                self.sd_log['ownedvehicles'] = self._sd('ownedvehicles')

                r: sqlite3.Cursor = cur.execute(
                    '''
                    SELECT elapseddays, cashbalance, onlinebalance, networth, lifetimeearnings, rank, tier, xp, totalxp, discoveredproducts, ownedbusinesses, ownedproperties, ownedvehicles
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
                del current['timeofday']

                if previous == current:
                    Screen.msg("no changes detected", ts=True)
                else:
                    Screen.msg("changes detected", ts=True)
                    cur.execute(
                        '''
                        INSERT INTO logs (log_time, save_id, gameversion, playtime, timeofday, elapseddays, cashbalance, onlinebalance, networth, lifetimeearnings, rank, tier, xp, totalxp, discoveredproducts, ownedbusinesses, ownedproperties, ownedvehicles)
                        VALUES (:log_time, :save_id, :gameversion, :playtime, :timeofday, :elapseddays, :cashbalance, :onlinebalance, :networth, :lifetimeearnings, :rank, :tier, :xp, :totalxp, :discoveredproducts, :ownedbusinesses, :ownedproperties, :ownedvehicles);
                        ''',
                        {
                            'log_time': time.time(),
                            **self.sd_profile,
                            **self.sd_log,
                        }
                    )
                    con.commit()
                    Screen.msg(f"updated {self.db_file.name} (save_id={self.sd_profile['save_id']} log_id={cur.lastrowid})", ts=True)

                    if len(self.args['export_current']) > 0:
                        self._export_current()

                    if len(self.args['export_history']) > 0:
                        self._export_history(db_cur=cur)

                Screen.msg()
                self._print_monitor_summary(previous=previous)
                Screen.msg()

                Screen.msg("next check in", sleep=self.args['check_interval'], ts=True)

            finally:
                con.close()


    def _print_monitor_summary(self, previous: dict):
        indent: int = max([len(k) for k in self.sd_log])
        Screen.msg(f"{'organisation':>{indent}}  {self.sd_profile['organisation']}")
        for k, v in self.sd_log.items():
            Screen.msg(f"{k:>{indent}}", end="  ")
            if k in previous.keys() and previous.get(k) != v:
                Screen.msg(f"{previous[k]} -> {v}", end=" ")
                Screen.msg(f"({(previous[k] - v) * -1})" if type(v) in [int, float] else "")
            else:
                Screen.msg(f"{v}")


    def _sd(self, col: str, /) -> str | int | float | None:
        default_organisation: str = ''
        default_seed: int = 0
        default_gameversion: str = ''
        default_playtime: int = 0
        default_timeofday: int = 0
        default_elapseddays: int = 0
        default_cashbalance: float = 0
        default_onlinebalance: float = 0
        default_networth: float = 0
        default_lifetimeearnings: float = 0
        default_rank: int = 0
        default_tier: int = 0
        default_xp: int = 0
        default_totalxp: int = 0
        default_discoveredproducts: int = 0
        default_ownedbusinesses: int = 0
        default_ownedproperties: int = 0
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

        if col == 'timeofday':
            data = self._sd_data('Time.json')
            if not data.get('TimeOfDay'):
                return default_timeofday
            return int(data['TimeOfDay'])

        if col == 'elapseddays':
            data = self._sd_data('Time.json')
            if not data.get('ElapsedDays'):
                return default_elapseddays
            return int(data['ElapsedDays'])

        if col == 'cashbalance':
            data = self._sd_data('Players/Player_0/Inventory.json')
            if not data.get('Items'):
                return default_cashbalance
            for item in data['Items']:
                item_data = json.loads(s=item) or {}
                if item_data.get('DataType') == 'CashData' and item_data.get('CashBalance'):
                    return float(item_data['CashBalance'])
            return default_cashbalance

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

        if col == 'ownedbusinesses':
            count: int | None = None
            data_files = self.save_dir.glob('Businesses/*.json')
            for file in data_files:
                data = self._sd_data(f'Businesses/{file.name}')
                if not data.get('IsOwned'):
                    continue
                if data['IsOwned']:
                    count = 1 if not count else count + 1
            if not count:
                return default_ownedbusinesses
            return count

        if col == 'ownedproperties':
            count: int | None = None
            data_files = self.save_dir.glob('Properties/*.json')
            for file in data_files:
                data = self._sd_data(f'Properties/{file.name}')
                if not data.get('IsOwned'):
                    continue
                if data['IsOwned']:
                    count = 1 if not count else count + 1
            if not count:
                return default_ownedproperties
            return count

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


    def _export_current(self) -> None:
        current_data: dict = {
            '_t': time.time(),
            **self.sd_profile,
            **self.sd_log,
        }

        file: Path | None = None
        data: str | None = None

        for export_type in self.args['export_current']:
            if export_type == 'json':
                file = self.current_json_export_file
                if len(self.args['export_keys']) == 0:
                    data = json.dumps(obj=current_data, indent=4)
                else:
                    dump: dict = {}
                    for k in self.args['export_keys']:
                        if current_data.get(k):
                            dump[k] = current_data[k]
                    data = json.dumps(obj=dump, indent=4)

            if export_type == 'txt':
                file = self.current_txt_export_file
                indent: int = 0
                if len(self.args['export_keys']) == 0:
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
                Screen.msg(f"updated {file.name}", ts=True)


    def _export_history(self, db_cur: sqlite3.Cursor) -> None:
        query: str
        if not self.args['history_limit']:
            query = '''
            SELECT *
            FROM logs
            WHERE save_id = :save_id
            ORDER BY log_id ASC;
            '''
        else:
            query = '''
            SELECT *
            FROM logs
            WHERE save_id = :save_id
            ORDER BY log_id DESC
            LIMIT :limit;
            '''

        r: sqlite3.Cursor = db_cur.execute(
            query,
            {
                **self.sd_profile,
                'limit': self.args['history_limit'],
            }
        )

        dump: list[sqlite3.Row] | None = r.fetchall()

        if self.args['history_limit']:
            dump.reverse()

        file: Path | None = None
        data: str | None = None

        for export_type in self.args['export_history']:
            if export_type == 'json':
                file = self.history_json_export_file
                data = json.dumps(obj=[dict(row) for row in dump])
                file.write_text(data)
                Screen.msg(f"updated {file.name}", ts=True)

            if export_type == 'csv':
                file = self.history_csv_export_file
                with open(file=file, mode='w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow([v[0] for v in db_cur.description])
                    writer.writerows(dump)
                    Screen.msg(f"updated {file.name}", ts=True)

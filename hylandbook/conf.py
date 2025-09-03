from pathlib import Path




class Conf:
    app_name: str = 'hylandbook'
    app_banner: str = f'--==[ {' '.join(app_name).upper()} ]==--'

    default_data_dir: Path = Path.cwd() / 'hb_data'

    db_file_name: str = 'book.db'

    default_check_interval: int = 60
    min_check_interval: int = 5

    sd_file_read_throttle: float = 0

    argparser: dict = {
        'init': {
            'prog': app_name,
            'description': "See the README for more.",
        },
        'args': [
            {
                'name_or_flags': ['save_dir'],
                'setup': {
                    'metavar': 'SAVEGAME_PATH',
                    'type': str,
                    'default': None,
                    'help': "path to a Schedule I 'SaveGame_*' directory, enclose it in quotes if it contains spaces, e.g. \"C:\\path to\\SaveGame_1\""
                },
            },
            {
                'name_or_flags': ['-i', '--check-interval'],
                'setup': {
                    'metavar': 'SECONDS',
                    'type': int,
                    'default': default_check_interval,
                    'help': f"how frequently to check the save data for changes, in seconds, default: {default_check_interval}, minimum: {min_check_interval}",
                },
            },
            {
                'name_or_flags': ['-d', '--data-dir'],
                'setup': {
                    'metavar': 'PATH',
                    'type': str,
                    'default': default_data_dir,
                    'help': f"path to directory where {app_name} will store data, default: {default_data_dir}",
                },
            },
        ],
    }

    db_schema: str = '''
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
            'ownedvehicles' INTEGER DEFAULT NULL,

            PRIMARY KEY('log_id' AUTOINCREMENT),
            FOREIGN KEY ('save_id') REFERENCES 'saves'('save_id')
        );

        COMMIT;
    '''

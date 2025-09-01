from pathlib import Path




APP_NAME: str = 'hylandbook'

APP_BANNER: str = '--==[ H Y L A N D B O O K ]==--\n'

DEFAULT_DATA_DIR: Path = Path.cwd() / 'hb_data'

DEFAULT_CHECK_INTERVAL: int = 60

MIN_CHECK_INTERVAL: int = 10

SD_FILE_READ_THROTTLE: float = 0

DATABASE_FILE_NAME: str = 'book.db'

DATABASE_SCHEMA: str = '''
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

ARGPARSER: dict = {
    'init': {
        'prog': APP_NAME,
        'description': "Please see the README for more.",
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
                'default': DEFAULT_CHECK_INTERVAL,
                'help': f"how frequently to check the save data for changes, in seconds, default: {DEFAULT_CHECK_INTERVAL}, minimum: {MIN_CHECK_INTERVAL}",
            },
        },
        {
            'name_or_flags': ['-d', '--data-dir'],
            'setup': {
                'metavar': 'PATH',
                'type': str,
                'default': DEFAULT_DATA_DIR,
                'help': f"path to directory where {APP_NAME} will store data, default: {DEFAULT_DATA_DIR}",
            },
        },
    ],
}

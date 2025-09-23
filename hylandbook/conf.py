from pathlib import Path




class Conf:
    app_name: str = 'hylandbook'
    app_banner: str = f'--==[ {' '.join(app_name).upper()} ]==--'

    default_data_dir: Path = Path.cwd() / 'hb_data'

    db_file_name: str = 'book.db'
    current_json_export_file_name: str = 'current.json'
    current_txt_export_file_name: str = 'current.txt'
    current_html_export_file_name: str = 'current.html'
    current_html_template_export_file_name: str = 'current_template.html'
    history_json_export_file_name: str = 'history.json'
    history_csv_export_file_name: str = 'history.csv'
    history_html_export_file_name: str = 'history.html'
    history_html_template_export_file_name: str = 'history_template.html'

    default_check_interval: int = 60
    min_check_interval: int = 10

    sd_file_read_throttle: float = 0

    default_current_export_types: list[str] = []
    current_export_types_choices: list[str] = [
        'json',
        'txt',
        'html',  # WIP
    ]

    default_history_export_types: list[str] = []
    history_export_types_choices: list[str] = [
        'json',
        'csv',
        'html',  # WIP
    ]
    min_history_limit: int = 1

    default_export_keys: list[str] = []
    export_keys_choices: list[str] = [
        '_t',
        'save_dir',
        'organisation',
        'seed',
        'save_id',
        'gameversion',
        'playtime',
        'timeofday',
        'elapseddays',
        'cashbalance',
        'onlinebalance',
        'networth',
        'lifetimeearnings',
        'rank',
        'tier',
        'xp',
        'totalxp',
        'discoveredproducts',
        'ownedbusinesses',
        'ownedproperties',
        'ownedvehicles',
    ]

    argparser: dict = {
        # TODO: copy over the README text so it's all the same
        'init': {
            'prog': app_name,
            'description': "SAVEGAME_PATH is required, options are optional and will use their defaults if not set by you. For more help see the README.",
            'epilog': 'Cool links: scheduleonegame.com, github.com/etrusci-org/hylandbook',
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
                'name_or_flags': ['-c', '--export-current'],
                'setup': {
                    'metavar': 'TYPE',
                    'type': str,
                    'nargs': '*',
                    'choices': current_export_types_choices,
                    'default': default_current_export_types,
                    'help': f"one or more types of current export files to update each time save data changes are detected, default: no export, choices: {' '.join(current_export_types_choices)}",
                },
            },
            {
                'name_or_flags': ['-y', '--export-history'],
                'setup': {
                    'metavar': 'TYPE',
                    'type': str,
                    'nargs': '*',
                    'choices': history_export_types_choices,
                    'default': default_history_export_types,
                    'help': f"one or more types of history export files to update each time save data changes are detected, default: no export, choices: {' '.join(history_export_types_choices)}",
                },
            },
            {
                'name_or_flags': ['-m', '--history-limit'],
                'setup': {
                    'metavar': 'NUMBER',
                    'type': int,
                    'default': None,
                    'help': f"limit the number of recent rows that are exported in history export files, default: no limit, minimum: {min_history_limit}",
                },
            },
            {
                'name_or_flags': ['-k', '--export-keys'],
                'setup': {
                    'metavar': 'KEY',
                    'type': str,
                    'nargs': '*',
                    'choices': export_keys_choices,
                    'default': default_export_keys,
                    'help': f"value keys of data to export, does currently not apply to history exports, default: all keys, choices: {' '.join(export_keys_choices)}",
                },
            },
            {
                'name_or_flags': ['-d', '--data-dir'],
                'setup': {
                    'metavar': 'PATH',
                    'type': str,
                    'default': default_data_dir,
                    'help': f"path to folder where {app_name} will save data, will be created automatically if it does not exist yet, default: <current working directory>\\hb_data, current: {default_data_dir}",
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
            'timeofday' INTEGER DEFAULT NULL,
            'elapseddays' INTEGER DEFAULT NULL,
            'cashbalance' REAL DEFAULT NULL,
            'onlinebalance' REAL DEFAULT NULL,
            'networth' REAL DEFAULT NULL,
            'lifetimeearnings' REAL DEFAULT NULL,
            'rank' INTEGER DEFAULT NULL,
            'tier' INTEGER DEFAULT NULL,
            'xp' INTEGER DEFAULT NULL,
            'totalxp' INTEGER DEFAULT NULL,
            'discoveredproducts' INTEGER DEFAULT NULL,
            'ownedbusinesses' INTEGER DEFAULT NULL,
            'ownedproperties' INTEGER DEFAULT NULL,
            'ownedvehicles' INTEGER DEFAULT NULL,

            PRIMARY KEY('log_id' AUTOINCREMENT),
            FOREIGN KEY ('save_id') REFERENCES 'saves'('save_id')
        );

        COMMIT;
    '''

    default_html_export_template: str = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HYLANDBOOK</title>
</head>
<body>
    <h1>HYLANDBOOK</h1>

    <!--
    Changes you make here will be reflected in the export file.
    To reset this template to it's default state, delete it and
    it will be created on the next startup.
    -->

    <script>
        // { HB_DATA } (in curly braces, without the spaces) will be replaced with
        // either a dict holding the 'current' data
        // or a list of dicts holding the 'history' data:
        const hb_data = {HB_DATA}

        // when done loading the page ...
        window.addEventListener('load', () => {
            // do something with hb_data
            console.log(hb_data)

            // reload the page/data every 60 seconds and then  ...
            setTimeout(() => window.location.reload(), 60 * 1_000)
        })
    </script>
</body>
</html>
    '''

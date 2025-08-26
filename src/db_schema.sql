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
    'playtime' INTEGER DEFAULT NULL, -- *
    'elapseddays' INTEGER DEFAULT NULL, -- *
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

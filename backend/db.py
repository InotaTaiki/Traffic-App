import os
import sqlite3

import config

os.makedirs(os.path.dirname(config.DB_PATH) or ".", exist_ok=True)
_conn = sqlite3.connect(config.DB_PATH, check_same_thread=False)

# Timestamps are UTC; derive hour/day-of-week (LA time) at training time.
_conn.executescript(
    """
    CREATE TABLE IF NOT EXISTS travel_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts TEXT NOT NULL,
        corridor TEXT NOT NULL,
        duration_s REAL NOT NULL,
        typical_s REAL,
        distance_m REAL NOT NULL,
        heavy_share REAL NOT NULL,
        incident_count INTEGER NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_travel_log_corridor_ts ON travel_log (corridor, ts);
    """
)


def insert_log(row):
    _conn.execute(
        "INSERT INTO travel_log (ts, corridor, duration_s, typical_s, distance_m, heavy_share, incident_count) "
        "VALUES (:ts, :corridor, :duration_s, :typical_s, :distance_m, :heavy_share, :incident_count)",
        row,
    )
    _conn.commit()
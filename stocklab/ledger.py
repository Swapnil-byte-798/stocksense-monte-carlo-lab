"""A small append-only experiment ledger; parameters and results stay together."""

import json
from pathlib import Path
import sqlite3


SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY,
    created_at TEXT NOT NULL,
    config_id TEXT NOT NULL,
    method TEXT NOT NULL,
    selected_order INTEGER NOT NULL,
    mean_profit REAL NOT NULL,
    tail_profit REAL NOT NULL,
    result_json TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_runs_config ON runs(config_id);
"""


def save(result, path="output/experiments.db"):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.executescript(SCHEMA)
        cursor = conn.execute(
            "INSERT INTO runs(created_at, config_id, method, selected_order, mean_profit, tail_profit, result_json) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (result["created_at"], result["config_id"], result["config"]["method"], result["selected"]["order"], result["selected"]["mean_profit"], result["selected"]["tail_profit"], json.dumps(result, allow_nan=False)),
        )
        return cursor.lastrowid


def recent(path="output/experiments.db", limit=20):
    if not Path(path).exists():
        return []
    with sqlite3.connect(path) as conn:
        conn.row_factory = sqlite3.Row
        return [dict(r) for r in conn.execute("SELECT id, created_at, config_id, method, selected_order, mean_profit, tail_profit FROM runs ORDER BY id DESC LIMIT ?", (limit,))]

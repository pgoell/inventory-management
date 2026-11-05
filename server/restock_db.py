"""SQLite store for submitted restocking orders, the only data that persists."""

import json
import os
import sqlite3

DB_PATH = os.environ.get(
    "RESTOCK_DB_PATH",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "restock.db"),
)


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with _connect() as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS restock_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                budget REAL NOT NULL,
                total_cost REAL NOT NULL,
                lead_time_days INTEGER NOT NULL,
                expected_delivery TEXT NOT NULL,
                items TEXT NOT NULL
            )"""
        )


def insert_order(order: dict) -> int:
    with _connect() as conn:
        cur = conn.execute(
            "INSERT INTO restock_orders (created_at, budget, total_cost, lead_time_days, expected_delivery, items)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (order["created_at"], order["budget"], order["total_cost"], order["lead_time_days"],
             order["expected_delivery"], json.dumps(order["items"])),
        )
        return cur.lastrowid


def list_orders() -> list:
    with _connect() as conn:
        rows = conn.execute("SELECT * FROM restock_orders ORDER BY id DESC").fetchall()
    return [{**dict(r), "items": json.loads(r["items"])} for r in rows]

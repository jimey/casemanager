import os
import sqlite3
from flask import g


DB_DIR = os.path.join(os.path.dirname(__file__), 'data')
DB_PATH = os.path.join(DB_DIR, 'app.db')


SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS patients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    gender TEXT,
    date_of_birth TEXT,
    phone TEXT,
    address TEXT,
    id_number TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS visits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL,
    visit_date TEXT,
    symptoms TEXT,
    diagnosis TEXT,
    treatment TEXT,
    doctor TEXT,
    notes TEXT,
    FOREIGN KEY(patient_id) REFERENCES patients(id) ON DELETE CASCADE
);
"""


def _connect():
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON;')
    return conn


def get_db():
    if 'db' not in g:
        g.db = _connect()
    return g.db


def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    os.makedirs(DB_DIR, exist_ok=True)
    with sqlite3.connect(DB_PATH) as db:
        db.executescript(SCHEMA_SQL)
        db.commit()


def ensure_initialized():
    # Ensure tables exist; initialize if missing
    if not os.path.exists(DB_PATH):
        init_db()
        return
    try:
        with sqlite3.connect(DB_PATH) as db:
            cur = db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='patients'")
            if not cur.fetchone():
                init_db()
    except sqlite3.Error:
        init_db()


def query_one(db, sql, params=()):
    cur = db.execute(sql, params)
    row = cur.fetchone()
    cur.close()
    return row


def query_all(db, sql, params=()):
    cur = db.execute(sql, params)
    rows = cur.fetchall()
    cur.close()
    return rows


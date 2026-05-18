from werkzeug.security import generate_password_hash, check_password_hash
import os
import sqlite3
from functools import wraps
from flask import Blueprint, g, current_app

try:
    import psycopg2
    import psycopg2.extras
except ImportError:
    psycopg2 = None

ml = Blueprint("ml", __name__)

class PostgresWrapper:
    def __init__(self, conn):
        self.conn = conn

    def execute(self, query, params=None):
        cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        # Convert SQLite placeholders to Postgres placeholders
        postgres_query = query.replace("?", "%s")
        if params:
            cur.execute(postgres_query, params)
        else:
            cur.execute(postgres_query)
        return cur

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def close(self):
        self.conn.close()

    def executescript(self, script):
        with self.conn.cursor() as cur:
            postgres_script = script.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "SERIAL PRIMARY KEY")
            cur.execute(postgres_script)
            self.conn.commit()

class SqliteWrapper:
    def __init__(self, conn):
        self.conn = conn

    def execute(self, query, params=None):
        cur = self.conn.cursor()
        if params:
            cur.execute(query, params)
        else:
            cur.execute(query)
        return cur

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def close(self):
        self.conn.close()

    def executescript(self, script):
        self.conn.executescript(script)


def get_db():
    """Open a database connection scoped to the request."""
    if "db" not in g:
        db_url = os.getenv("DATABASE_URL")
        if db_url and psycopg2:
            # Use PostgreSQL if DATABASE_URL is set
            conn = psycopg2.connect(db_url)
            g.db = PostgresWrapper(conn)
        else:
            # Fallback to local SQLite
            db_path = os.path.join(current_app.instance_path, "agrosmart.db")
            conn = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA foreign_keys=ON")
            g.db = SqliteWrapper(conn)
    return g.db


def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """Create tables if they don't exist."""
    db = get_db()
    db.executescript("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    email TEXT UNIQUE,
    phone TEXT UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS contact (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    subject TEXT NOT NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""")
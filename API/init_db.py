"""Initialize the SQLite database from db_init.sql

Usage:
    python init_db.py

This will create (or update) `uil_tutor.db` in the project root.
"""
import sqlite3
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT.parent / 'uil_tutor.db'
SQL_PATH = ROOT / 'db_init.sql'


def run_sql_file(db_path: Path, sql_file: Path):
    if not sql_file.exists():
        print(f"SQL file not found: {sql_file}")
        return 1

    with sql_file.open('r', encoding='utf-8') as f:
        sql = f.read()

    conn = sqlite3.connect(str(db_path))
    try:
        conn.executescript(sql)
        conn.commit()
        print(f"Database initialized at: {db_path}")
    except Exception as e:
        print(f"Error initializing database: {e}")
        return 2
    finally:
        conn.close()

    return 0


if __name__ == '__main__':
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    rc = run_sql_file(DB_PATH, SQL_PATH)
    sys.exit(rc)

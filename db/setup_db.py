import sqlite3
import os

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DB_PATH = os.path.join(ROOT_DIR, 'arbeitslosigkeit.db')
SQL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'V1__init_schema.sql')


def setup_database():
    with open(SQL_PATH, 'r', encoding='utf-8') as f:
        sql_script = f.read()
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.executescript(sql_script)
        conn.commit()
        print(f"Datenbank erstellt: {DB_PATH}")
    finally:
        conn.close()


if __name__ == '__main__':
    setup_database()

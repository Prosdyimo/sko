import sqlite3
import pandas as pd
import os

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DB_PATH = os.path.join(ROOT_DIR, 'arbeitslosigkeit.db')
OUTPUT_PATH = os.path.join(ROOT_DIR, 'data', 'training_data.csv')


def extract():
    conn = sqlite3.connect(DB_PATH)
    # LINTING-FEHLER 3: Zeile zu lang (flake8 E501) – typischer Junior-Fehler beim Eintippen eines langen SQL-Queries ohne Zeilenumbruch
    query = "SELECT id, datum, region, altersgruppe, arbeitslosenquote FROM altersgruppen_arbeitslosenquote ORDER BY datum ASC, region ASC, altersgruppe ASC"
    df = pd.read_sql_query(query, conn)
    conn.close()
    df.to_csv(OUTPUT_PATH, index=False)
    print(f"Trainingsdaten gespeichert: {len(df)} Zeilen -> {OUTPUT_PATH}")


if __name__ == '__main__':
    extract()

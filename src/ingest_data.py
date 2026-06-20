import sqlite3
import pandas as pd
import os

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DB_PATH = os.path.join(ROOT_DIR, 'arbeitslosigkeit.db')
EXCEL_ALT = os.path.join(ROOT_DIR, 'data', '2.1 Arbeitslosenquoten.xlsx')
EXCEL_JUG = os.path.join(ROOT_DIR, 'data', '2.2 Jugendarbeitslosenquoten.xlsx')


def _load_altersgruppen(conn):
    df = pd.read_excel(EXCEL_ALT)
    meta_cols = ['Sprachregion', 'Gruppen']
    date_cols = [c for c in df.columns if hasattr(c, 'year')]
    df_long = df.melt(
        id_vars=meta_cols, value_vars=date_cols,
        var_name='datum_raw', value_name='arbeitslosenquote'
    )
    dates = pd.to_datetime(df_long['datum_raw'])
    df_long['datum'] = dates.dt.strftime('%Y-%m')
    n_rows = len(df_long)
    records = list(zip(
        df_long['datum'],
        df_long['Sprachregion'],
        df_long['Gruppen'],
        df_long['arbeitslosenquote'].astype(float)
    ))
    conn.executemany(
        "INSERT INTO altersgruppen_arbeitslosenquote "
        "(datum, region, altersgruppe, arbeitslosenquote) VALUES (?, ?, ?, ?)",
        records
    )
    return n_rows


def _load_jugendliche(conn):
    df = pd.read_excel(EXCEL_JUG)
    meta_cols = ['Sprachregion', 'Geschlecht', 'Gruppen']
    date_cols = [c for c in df.columns if hasattr(c, 'year')]
    df_long = df.melt(
        id_vars=meta_cols, value_vars=date_cols,
        var_name='datum_raw', value_name='arbeitslosenquote'
    )
    dates = pd.to_datetime(df_long['datum_raw'])
    df_long['datum'] = dates.dt.strftime('%Y-%m')
    n_rows = len(df_long)
    records = list(zip(
        df_long['datum'],
        df_long['Sprachregion'],
        df_long['Geschlecht'],
        df_long['arbeitslosenquote'].astype(float)
    ))
    conn.executemany(
        "INSERT INTO jugendliche_arbeitslosenquote "
        "(datum, region, geschlecht, arbeitslosenquote) VALUES (?, ?, ?, ?)",
        records
    )
    return n_rows


def ingest():
    conn = sqlite3.connect(DB_PATH)
    try:
        n_alt = _load_altersgruppen(conn)
        n_jug = _load_jugendliche(conn)
        conn.commit()
        print(
            f"Ingestion: {n_alt} Altersgruppen- und "
            f"{n_jug} Jugendlichen-Zeilen geschrieben."
        )
    finally:
        conn.close()


if __name__ == '__main__':
    ingest()

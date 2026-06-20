import sqlite3
import pandas as pd
import pytest
from unittest.mock import patch
from src.ingest_data import _load_altersgruppen, _load_jugendliche, ingest


# ---------------------------------------------------------------------------
# Hilfsfunktion: In-Memory-DB mit korrektem Schema anlegen
# ---------------------------------------------------------------------------

def _make_db():
    conn = sqlite3.connect(':memory:')
    conn.execute("""
        CREATE TABLE altersgruppen_arbeitslosenquote (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            datum             TEXT    NOT NULL,
            region            TEXT    NOT NULL,
            altersgruppe      TEXT    NOT NULL,
            arbeitslosenquote REAL    NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE jugendliche_arbeitslosenquote (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            datum             TEXT    NOT NULL,
            region            TEXT    NOT NULL,
            geschlecht        TEXT    NOT NULL,
            arbeitslosenquote REAL    NOT NULL
        )
    """)
    return conn


# ---------------------------------------------------------------------------
# Unit-Test: _load_altersgruppen
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_load_altersgruppen_inserts_rows():
    """Prüft ob _load_altersgruppen die Zeilen korrekt transformiert und einfügt."""
    # Fake-DataFrame: Sprachregion + Gruppen + eine Datumsspalte (Timestamp hat .year)
    datum_col = pd.Timestamp('2024-01-01')
    fake_df = pd.DataFrame({
        'Sprachregion': ['Deutsche Schweiz', 'Romandie'],
        'Gruppen':      ['25-49 Jahre',       '25-49 Jahre'],
        datum_col:      [4.5,                  6.1],
    })

    conn = _make_db()
    with patch('src.ingest_data.pd.read_excel', return_value=fake_df):
        n = _load_altersgruppen(conn)

    assert n == 2
    rows = conn.execute(
        "SELECT datum, region, altersgruppe, arbeitslosenquote "
        "FROM altersgruppen_arbeitslosenquote ORDER BY region"
    ).fetchall()
    assert len(rows) == 2
    # Datum muss als 'YYYY-MM' gespeichert werden
    assert rows[0][0] == '2024-01'
    assert rows[0][1] == 'Deutsche Schweiz'
    assert rows[0][2] == '25-49 Jahre'
    assert rows[0][3] == pytest.approx(4.5)
    conn.close()


@pytest.mark.unit
def test_load_altersgruppen_returns_row_count():
    """Rückgabewert muss der Anzahl einzufügender Zeilen entsprechen."""
    datum_col = pd.Timestamp('2023-06-01')
    fake_df = pd.DataFrame({
        'Sprachregion': ['Tessin'],
        'Gruppen':      ['15-24 Jahre'],
        datum_col:      [9.0],
    })
    conn = _make_db()
    with patch('src.ingest_data.pd.read_excel', return_value=fake_df):
        n = _load_altersgruppen(conn)
    assert n == 1
    conn.close()


# ---------------------------------------------------------------------------
# Unit-Test: _load_jugendliche
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_load_jugendliche_inserts_rows():
    """Prüft ob _load_jugendliche Geschlecht-Spalte korrekt verarbeitet."""
    datum_col = pd.Timestamp('2024-03-01')
    fake_df = pd.DataFrame({
        'Sprachregion': ['Deutsche Schweiz'],
        'Geschlecht':   ['Männer'],
        'Gruppen':      ['15-24 Jahre'],
        datum_col:      [8.2],
    })

    conn = _make_db()
    with patch('src.ingest_data.pd.read_excel', return_value=fake_df):
        n = _load_jugendliche(conn)

    assert n == 1
    row = conn.execute(
        "SELECT datum, region, geschlecht, arbeitslosenquote "
        "FROM jugendliche_arbeitslosenquote"
    ).fetchone()
    assert row[0] == '2024-03'
    assert row[1] == 'Deutsche Schweiz'
    assert row[2] == 'Männer'
    assert row[3] == pytest.approx(8.2)
    conn.close()


@pytest.mark.unit
def test_load_jugendliche_multiple_date_columns():
    """Mehrere Datumsspalten erzeugen mehrere Zeilen (melt)."""
    d1 = pd.Timestamp('2023-01-01')
    d2 = pd.Timestamp('2023-02-01')
    fake_df = pd.DataFrame({
        'Sprachregion': ['Romandie'],
        'Geschlecht':   ['Frauen'],
        'Gruppen':      ['15-24 Jahre'],
        d1:             [7.0],
        d2:             [7.5],
    })
    conn = _make_db()
    with patch('src.ingest_data.pd.read_excel', return_value=fake_df):
        n = _load_jugendliche(conn)
    assert n == 2
    conn.close()


@pytest.mark.unit
def test_ingest_calls_loaders_commit_and_close(capsys):
    """ingest() muss Loader aufrufen, committen und Verbindung schliessen."""
    with patch('src.ingest_data.sqlite3.connect') as connect_mock, \
         patch('src.ingest_data._load_altersgruppen', return_value=2) as load_alt_mock, \
         patch('src.ingest_data._load_jugendliche', return_value=3) as load_jug_mock:
        conn = connect_mock.return_value
        ingest()

    load_alt_mock.assert_called_once_with(conn)
    load_jug_mock.assert_called_once_with(conn)
    conn.commit.assert_called_once()
    conn.close.assert_called_once()
    out = capsys.readouterr().out
    assert 'Ingestion: 2 Altersgruppen- und 3 Jugendlichen-Zeilen geschrieben.' in out


# ---------------------------------------------------------------------------
# Integration-Test: ingest()
# ---------------------------------------------------------------------------

@pytest.mark.integration
@pytest.mark.db
def test_ingest_commits_to_db(tmp_path, capsys):
    """Prüft den kompletten ingest()-Durchlauf mit gepatchter DB und Excel-Dateien."""
    db_path = tmp_path / 'test.db'

    # DB-Schema initialisieren
    conn_setup = sqlite3.connect(db_path)
    conn_setup.execute("""
        CREATE TABLE altersgruppen_arbeitslosenquote (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            datum TEXT, region TEXT, altersgruppe TEXT, arbeitslosenquote REAL
        )
    """)
    conn_setup.execute("""
        CREATE TABLE jugendliche_arbeitslosenquote (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            datum TEXT, region TEXT, geschlecht TEXT, arbeitslosenquote REAL
        )
    """)
    conn_setup.commit()
    conn_setup.close()

    datum_col = pd.Timestamp('2024-06-01')
    fake_alt = pd.DataFrame({
        'Sprachregion': ['Deutsche Schweiz'],
        'Gruppen':      ['25-49 Jahre'],
        datum_col:      [3.8],
    })
    fake_jug = pd.DataFrame({
        'Sprachregion': ['Romandie'],
        'Geschlecht':   ['Männer'],
        'Gruppen':      ['15-24 Jahre'],
        datum_col:      [10.1],
    })

    with patch('src.ingest_data.DB_PATH', str(db_path)), \
         patch('src.ingest_data.pd.read_excel', side_effect=[fake_alt, fake_jug]):
        ingest()

    # Ausgabe prüfen
    out = capsys.readouterr().out
    assert 'Ingestion' in out
    assert '1' in out

    # DB-Inhalt prüfen
    conn = sqlite3.connect(db_path)
    n_alt = conn.execute(
        "SELECT COUNT(*) FROM altersgruppen_arbeitslosenquote"
    ).fetchone()[0]
    n_jug = conn.execute(
        "SELECT COUNT(*) FROM jugendliche_arbeitslosenquote"
    ).fetchone()[0]
    conn.close()
    assert n_alt == 1
    assert n_jug == 1

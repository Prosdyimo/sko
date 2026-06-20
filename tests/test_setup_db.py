import sqlite3
import pytest
from unittest.mock import patch
from db.setup_db import setup_database


# ---------------------------------------------------------------------------
# Integration-Tests: setup_database()
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_setup_creates_both_tables(tmp_path):
    """setup_database() muss beide Tabellen anlegen."""
    db_path = tmp_path / 'test.db'

    with patch('db.setup_db.DB_PATH', str(db_path)):
        setup_database()

    conn = sqlite3.connect(db_path)
    tables = {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }
    conn.close()

    assert 'altersgruppen_arbeitslosenquote' in tables
    assert 'jugendliche_arbeitslosenquote' in tables


@pytest.mark.unit
def test_setup_altersgruppen_table_columns(tmp_path):
    """Tabelle altersgruppen_arbeitslosenquote muss die korrekten Spalten haben."""
    db_path = tmp_path / 'test.db'

    with patch('db.setup_db.DB_PATH', str(db_path)):
        setup_database()

    conn = sqlite3.connect(db_path)
    cols = {row[1] for row in conn.execute(
        "PRAGMA table_info(altersgruppen_arbeitslosenquote)"
    ).fetchall()}
    conn.close()

    assert cols == {'id', 'datum', 'region', 'altersgruppe', 'arbeitslosenquote'}


@pytest.mark.unit
def test_setup_jugendliche_table_columns(tmp_path):
    """Tabelle jugendliche_arbeitslosenquote muss die korrekten Spalten haben."""
    db_path = tmp_path / 'test.db'

    with patch('db.setup_db.DB_PATH', str(db_path)):
        setup_database()

    conn = sqlite3.connect(db_path)
    cols = {row[1] for row in conn.execute(
        "PRAGMA table_info(jugendliche_arbeitslosenquote)"
    ).fetchall()}
    conn.close()

    assert cols == {'id', 'datum', 'region', 'geschlecht', 'arbeitslosenquote'}


@pytest.mark.unit
def test_setup_prints_output(tmp_path, capsys):
    """setup_database() muss eine Erfolgsmeldung ausgeben."""
    db_path = tmp_path / 'test.db'

    with patch('db.setup_db.DB_PATH', str(db_path)):
        setup_database()

    out = capsys.readouterr().out
    assert 'Datenbank erstellt' in out


@pytest.mark.unit
def test_setup_is_idempotent(tmp_path):
    """Zweimaliger Aufruf darf keinen Fehler werfen (CREATE TABLE IF NOT EXISTS)."""
    db_path = tmp_path / 'test.db'

    with patch('db.setup_db.DB_PATH', str(db_path)):
        setup_database()
        setup_database()  # zweiter Aufruf darf nicht scheitern

    conn = sqlite3.connect(db_path)
    n = conn.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name != 'sqlite_sequence'"
    ).fetchone()[0]
    conn.close()

    assert n == 2

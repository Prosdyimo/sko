import sqlite3
from unittest.mock import patch

import pandas as pd
import pytest

from db.setup_db import setup_database
from src.extract_data import extract
from src.ingest_data import ingest
from src.predict import predict
from src.train import train


def _build_ingest_frames():
    jan = pd.Timestamp("2024-01-01")
    feb = pd.Timestamp("2024-02-01")

    altersgruppen = pd.DataFrame(
        {
            "Sprachregion": ["Deutsche Schweiz", "Romandie"],
            "Gruppen": ["25-49 Jahre", "15-24 Jahre"],
            jan: [3.8, 5.2],
            feb: [3.9, 5.1],
        }
    )
    jugendliche = pd.DataFrame(
        {
            "Sprachregion": ["Deutsche Schweiz", "Romandie"],
            "Geschlecht": ["Männer", "Frauen"],
            "Gruppen": ["15-24 Jahre", "15-24 Jahre"],
            jan: [8.4, 7.8],
            feb: [8.1, 7.5],
        }
    )
    return altersgruppen, jugendliche


@pytest.mark.smoke
@pytest.mark.integration
@pytest.mark.db
@pytest.mark.acceptance
def test_pipeline_smoke_runs_end_to_end(tmp_path, capsys):
    db_path = tmp_path / "arbeitslosigkeit.db"
    training_path = tmp_path / "training_data.csv"
    model_path = tmp_path / "models" / "model.pkl"
    altersgruppen_df, jugendliche_df = _build_ingest_frames()

    with patch("db.setup_db.DB_PATH", str(db_path)):
        setup_database()

    with patch("src.ingest_data.DB_PATH", str(db_path)), patch(
        "src.ingest_data.pd.read_excel",
        side_effect=[altersgruppen_df, jugendliche_df],
    ):
        ingest()

    with patch("src.extract_data.DB_PATH", str(db_path)), patch(
        "src.extract_data.OUTPUT_PATH", str(training_path)
    ):
        extract()

    with patch("src.train.DATA_PATH", str(training_path)), patch(
        "src.train.MODEL_PATH", str(model_path)
    ):
        train()

    with patch("src.predict.MODEL_PATH", str(model_path)):
        predict()

    out = capsys.readouterr().out
    assert "Datenbank erstellt" in out
    assert "Ingestion:" in out
    assert "Trainingsdaten gespeichert" in out
    assert "Modell gespeichert" in out
    assert "Vorhersage:" in out
    assert training_path.exists()
    assert model_path.exists()

    conn = sqlite3.connect(db_path)
    try:
        n_altersgruppen = conn.execute(
            "SELECT COUNT(*) FROM altersgruppen_arbeitslosenquote"
        ).fetchone()[0]
        n_jugendliche = conn.execute(
            "SELECT COUNT(*) FROM jugendliche_arbeitslosenquote"
        ).fetchone()[0]
    finally:
        conn.close()

    assert n_altersgruppen == 4
    assert n_jugendliche == 4


@pytest.mark.regression
@pytest.mark.integration
@pytest.mark.db
def test_extract_writes_rows_in_stable_sorted_order(tmp_path):
    db_path = tmp_path / "arbeitslosigkeit.db"
    output_path = tmp_path / "training_data.csv"

    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            """
            CREATE TABLE altersgruppen_arbeitslosenquote (
                id INTEGER,
                datum TEXT,
                region TEXT,
                altersgruppe TEXT,
                arbeitslosenquote REAL
            )
            """
        )
        conn.executemany(
            """
            INSERT INTO altersgruppen_arbeitslosenquote
            (id, datum, region, altersgruppe, arbeitslosenquote)
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                (1, "2024-02", "Romandie", "25-49 Jahre", 5.1),
                (2, "2024-01", "Deutsche Schweiz", "15-24 Jahre", 4.0),
                (3, "2024-01", "Deutsche Schweiz", "25-49 Jahre", 3.5),
            ],
        )
        conn.commit()
    finally:
        conn.close()

    with patch("src.extract_data.DB_PATH", str(db_path)), patch(
        "src.extract_data.OUTPUT_PATH", str(output_path)
    ):
        extract()

    exported = pd.read_csv(output_path)
    actual_order = exported[["datum", "region", "altersgruppe"]].to_dict("records")

    assert actual_order == [
        {
            "datum": "2024-01",
            "region": "Deutsche Schweiz",
            "altersgruppe": "15-24 Jahre",
        },
        {
            "datum": "2024-01",
            "region": "Deutsche Schweiz",
            "altersgruppe": "25-49 Jahre",
        },
        {
            "datum": "2024-02",
            "region": "Romandie",
            "altersgruppe": "25-49 Jahre",
        },
    ]
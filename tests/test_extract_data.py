from unittest.mock import patch
import sqlite3
import pandas as pd
from src.extract_data import extract


def test_extract_creates_csv(tmp_path):
    db_path = tmp_path / "test.db"
    output_csv = tmp_path / "training_data.csv"

    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE altersgruppen_arbeitslosenquote (
            id INTEGER,
            datum TEXT,
            region TEXT,
            altersgruppe TEXT,
            arbeitslosenquote REAL
        )
    """)
    conn.execute("""
        INSERT INTO altersgruppen_arbeitslosenquote
        VALUES (1, '2024-01', 'Berlin', '18-25', 5.1)
    """)
    conn.commit()
    conn.close()

    with patch('src.extract_data.DB_PATH', str(db_path)), \
         patch('src.extract_data.OUTPUT_PATH', str(output_csv)):
        extract()

    assert output_csv.exists()
    df = pd.read_csv(output_csv)
    assert len(df) == 1
    assert df.iloc[0]['region'] == 'Berlin'
    assert df.iloc[0]['arbeitslosenquote'] == 5.1
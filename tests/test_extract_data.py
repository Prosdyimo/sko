from unittest.mock import patch
import sqlite3
import pandas as pd
import pytest
from src.extract_data import extract


@pytest.mark.unit
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


@pytest.mark.unit
def test_extract_calls_sql_and_writes_expected_path(tmp_path):
    output_csv = tmp_path / "out.csv"
    fake_df = pd.DataFrame([
        {
            'id': 1,
            'datum': '2024-01',
            'region': 'Romandie',
            'altersgruppe': '15-24',
            'arbeitslosenquote': 4.2,
        }
    ])

    with patch('src.extract_data.sqlite3.connect') as connect_mock, \
         patch('src.extract_data.pd.read_sql_query', return_value=fake_df) as read_sql_mock, \
         patch('src.extract_data.DB_PATH', 'dummy.db'), \
         patch('src.extract_data.OUTPUT_PATH', str(output_csv)), \
         patch.object(fake_df, 'to_csv') as to_csv_mock:
        extract()

    connect_mock.assert_called_once_with('dummy.db')
    read_sql_mock.assert_called_once()
    to_csv_mock.assert_called_once_with(str(output_csv), index=False)
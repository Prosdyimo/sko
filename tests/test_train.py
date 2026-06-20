import pickle
import numpy as np
import pandas as pd
from unittest.mock import patch
from src.train import train


# ---------------------------------------------------------------------------
# Hilfsfunktion: minimale Trainings-CSV in tmp_path schreiben
# ---------------------------------------------------------------------------

def _write_training_csv(path):
    df = pd.DataFrame({
        'datum':             ['2020-01', '2020-02', '2021-01', '2021-02',
                              '2022-01', '2022-02', '2023-01', '2023-02'],
        'region':            ['Deutsche Schweiz'] * 4 + ['Romandie'] * 4,
        'altersgruppe':      ['25-49 Jahre', '15-24 Jahre'] * 4,
        'arbeitslosenquote': [3.0, 4.5, 3.2, 4.8, 2.8, 4.2, 3.1, 4.6],
    })
    df.to_csv(path, index=False)


# ---------------------------------------------------------------------------
# Integration-Tests: train()
# ---------------------------------------------------------------------------

def test_train_creates_model_file(tmp_path):
    """train() muss eine model.pkl-Datei erstellen."""
    csv_path = tmp_path / 'training_data.csv'
    model_path = tmp_path / 'models' / 'model.pkl'
    _write_training_csv(csv_path)

    with patch('src.train.DATA_PATH', str(csv_path)), \
         patch('src.train.MODEL_PATH', str(model_path)):
        train()

    assert model_path.exists()


def test_train_model_pickle_has_expected_keys(tmp_path):
    """Das gespeicherte Pickle muss 'model', 'le_region' und 'le_gruppe' enthalten."""
    csv_path = tmp_path / 'training_data.csv'
    model_path = tmp_path / 'models' / 'model.pkl'
    _write_training_csv(csv_path)

    with patch('src.train.DATA_PATH', str(csv_path)), \
         patch('src.train.MODEL_PATH', str(model_path)):
        train()

    with open(model_path, 'rb') as f:
        model_data = pickle.load(f)

    assert 'model' in model_data
    assert 'le_region' in model_data
    assert 'le_gruppe' in model_data


def test_train_prints_r2_and_path(tmp_path, capsys):
    """Ausgabe muss R2-Score und gespeicherten Pfad melden."""
    csv_path = tmp_path / 'training_data.csv'
    model_path = tmp_path / 'models' / 'model.pkl'
    _write_training_csv(csv_path)

    with patch('src.train.DATA_PATH', str(csv_path)), \
         patch('src.train.MODEL_PATH', str(model_path)):
        train()

    out = capsys.readouterr().out
    assert 'R2-Score' in out
    assert 'Modell gespeichert' in out


def test_train_model_can_predict(tmp_path):
    """Das trainierte Modell muss für bekannte Label-Klassen einen float liefern."""
    csv_path = tmp_path / 'training_data.csv'
    model_path = tmp_path / 'models' / 'model.pkl'
    _write_training_csv(csv_path)

    with patch('src.train.DATA_PATH', str(csv_path)), \
         patch('src.train.MODEL_PATH', str(model_path)):
        train()

    with open(model_path, 'rb') as f:
        md = pickle.load(f)

    region_enc = md['le_region'].transform(['Deutsche Schweiz'])[0]
    gruppe_enc = md['le_gruppe'].transform(['25-49 Jahre'])[0]
    X = np.array([[2025, 6, region_enc, gruppe_enc]])
    pred = md['model'].predict(X)[0]

    assert isinstance(float(pred), float)

import pickle
import re
import pytest
import pandas as pd
from unittest.mock import patch
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import LabelEncoder
from src.predict import predict


# ---------------------------------------------------------------------------
# Hilfsfunktion: echtes Fake-Modell in tmp_path schreiben
# ---------------------------------------------------------------------------

def _write_fake_model(path):
    model = LinearRegression()
    features = pd.DataFrame(
        [[2020, 1, 0, 0], [2021, 6, 0, 0], [2022, 3, 0, 0], [2023, 9, 0, 0]],
        columns=['jahr', 'monat', 'region_enc', 'gruppe_enc'],
    )
    model.fit(features, [3.0, 3.5, 2.8, 3.2])
    le_region = LabelEncoder()
    le_gruppe = LabelEncoder()
    le_region.fit(['Deutsche Schweiz'])
    le_gruppe.fit(['25-49 Jahre'])
    model_data = {'model': model, 'le_region': le_region, 'le_gruppe': le_gruppe}
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'wb') as f:
        pickle.dump(model_data, f)


# ---------------------------------------------------------------------------
# Unit-Tests: predict()
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_predict_prints_region_and_year(tmp_path, capsys):
    """Ausgabe muss Region und Jahr enthalten."""
    model_path = tmp_path / 'models' / 'model.pkl'
    _write_fake_model(model_path)

    with patch('src.predict.MODEL_PATH', str(model_path)):
        predict()

    out = capsys.readouterr().out
    assert 'Deutsche Schweiz' in out
    assert '2025' in out


@pytest.mark.unit
def test_predict_output_contains_percentage(tmp_path, capsys):
    """Ausgabe muss einen Prozentwert im Format '0.00%' enthalten."""
    model_path = tmp_path / 'models' / 'model.pkl'
    _write_fake_model(model_path)

    with patch('src.predict.MODEL_PATH', str(model_path)):
        predict()

    out = capsys.readouterr().out
    assert re.search(r'\d+\.\d{2}%', out), f"Kein Prozentwert in Ausgabe: {out!r}"


@pytest.mark.unit
def test_predict_raises_if_model_missing():
    """Fehlende Modelldatei muss FileNotFoundError auslösen."""
    with patch('src.predict.MODEL_PATH', '/nonexistent/path/model.pkl'):
        with pytest.raises(FileNotFoundError):
            predict()

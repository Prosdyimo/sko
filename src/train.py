import os
import sys  # LINTING-FEHLER 4: ungenutzter Import (flake8 F401)
import pickle
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import LabelEncoder

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATA_PATH = os.path.join(ROOT_DIR, 'data', 'training_data.csv')
MODEL_PATH = os.path.join(ROOT_DIR, 'models', 'model.pkl')


def train():
    df = pd.read_csv(DATA_PATH)
    df['jahr'] = df['datum'].str[:4].astype(int)
    df['monat'] = df['datum'].str[5:7].astype(int)

    le_region = LabelEncoder()
    le_gruppe = LabelEncoder()
    df['region_enc'] = le_region.fit_transform(df['region'])
    df['gruppe_enc'] = le_gruppe.fit_transform(df['altersgruppe'])

    features = ['jahr', 'monat', 'region_enc', 'gruppe_enc']
    X = df[features]
    y = df['arbeitslosenquote']

    model = LinearRegression()
    model.fit(X, y)

    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    model_data = {
        'model': model, 'le_region': le_region, 'le_gruppe': le_gruppe
    }
    with open(MODEL_PATH, 'wb') as f:
        pickle.dump(model_data, f)

    print(f"Modell gespeichert: {MODEL_PATH}")
    print(f"R2-Score (Training): {model.score(X, y):.4f}")


if __name__ == '__main__':
    train()

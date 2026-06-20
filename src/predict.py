import os
import pickle
import numpy as np
import pandas as pd

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
MODEL_PATH = os.path.join(ROOT_DIR, 'models', 'model.pkl')


def predict():
    with open(MODEL_PATH, 'rb') as f:
        model_data = pickle.load(f)

    model = model_data['model']
    le_region = model_data['le_region']
    le_gruppe = model_data['le_gruppe']

    # Hardcodierte Dummy-Werte fuer eine Vorhersage
    jahr = 2025
    monat = 6
    region = 'Deutsche Schweiz'
    altersgruppe = '25-49 Jahre'

    region_enc = le_region.transform([region])[0]
    gruppe_enc = le_gruppe.transform([altersgruppe])[0]

    X_pred = pd.DataFrame(
        np.array([[jahr, monat, region_enc, gruppe_enc]]),
        columns=['jahr', 'monat', 'region_enc', 'gruppe_enc'],
    )
    vorhersage = model.predict(X_pred)[0]

    print(
        f"Vorhersage: {region}, {altersgruppe}, {monat}/{jahr} "
        f"-> Arbeitslosenquote: {vorhersage:.2f}%"
    )


if __name__ == '__main__':
    predict()

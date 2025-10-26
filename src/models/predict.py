from pathlib import Path

import joblib
import numpy as np

_model = None


def load_model(path: str):
    global _model
    _model = joblib.load(Path(path))


def predict(features):
    X = np.array([features], dtype=float)
    proba = None
    if hasattr(_model, "predict_proba"):
        proba = float(np.max(_model.predict_proba(X)))
    label = int(_model.predict(X)[0])
    return label, (proba if proba is not None else 1.0)

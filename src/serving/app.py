from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from ..models.predict import load_model, predict


class PredictIn(BaseModel):
    features: list[float] = Field(..., description="Feature vector")


class PredictOut(BaseModel):
    label: int
    proba: float


app = FastAPI(title="MLOps Serving")


@app.on_event("startup")
def _startup():
    path = Path("artifacts/model.joblib")
    if not path.exists():
        raise RuntimeError("model not found. run pipeline first.")
    load_model(str(path))


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/predict", response_model=PredictOut)
def _predict(payload: PredictIn):
    try:
        label, proba = predict(payload.features)
        return PredictOut(label=label, proba=proba)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

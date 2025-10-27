from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import hydra
import joblib
import pandas as pd
from omegaconf import DictConfig
from sklearn.metrics import accuracy_score


def _write_metrics(path: Path, metrics: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(metrics, indent=2))


@hydra.main(config_path="../../configs", config_name="config", version_base=None)
def main(cfg: DictConfig):
    thresholds = {m: None for m in cfg.eval.metrics}
    thresholds.update(cfg.eval.thresholds or {})
    model = joblib.load(Path(cfg.artifacts_dir) / "model.joblib")
    df = pd.read_parquet(cfg.data.features_path)
    X = df.drop(columns=[cfg.train.target]).values
    y = df[cfg.train.target].values
    acc = accuracy_score(y, model.predict(X))
    metrics = {"accuracy": acc}
    metrics_path = Path(cfg.artifacts_dir) / "metrics.json"
    _write_metrics(metrics_path, metrics)
    print(f"eval_accuracy={acc:.4f}")
    if thresholds.get("accuracy") and acc < thresholds["accuracy"]:
        raise SystemExit(f"accuracy {acc:.3f} < threshold {thresholds['accuracy']}")
    return 0


if __name__ == "__main__":
    main()

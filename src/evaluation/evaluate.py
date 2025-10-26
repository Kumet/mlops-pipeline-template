from pathlib import Path

import hydra
import joblib
import pandas as pd
from omegaconf import DictConfig
from sklearn.metrics import accuracy_score


@hydra.main(config_path="../../configs", config_name="config", version_base=None)
def main(cfg: DictConfig):
    thresholds = {m: None for m in cfg.eval.metrics}
    thresholds.update(cfg.eval.thresholds or {})
    model = joblib.load(Path(cfg.artifacts_dir) / "model.joblib")
    df = pd.read_parquet(cfg.data.features_path)
    X = df.drop(columns=["target"]).values
    y = df["target"].values
    acc = accuracy_score(y, model.predict(X))
    print(f"eval_accuracy={acc:.4f}")
    if thresholds.get("accuracy") and acc < thresholds["accuracy"]:
        raise SystemExit(f"accuracy {acc:.3f} < threshold {thresholds['accuracy']}")
    return 0


if __name__ == "__main__":
    main()

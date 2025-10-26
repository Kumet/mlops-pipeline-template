from pathlib import Path

import hydra
import joblib
import mlflow
import pandas as pd
from omegaconf import DictConfig
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split


@hydra.main(config_path="../../configs", config_name="config", version_base=None)
def main(cfg: DictConfig):
    mlflow.set_tracking_uri(cfg.mlflow.tracking_uri)
    mlflow.set_experiment("training")
    data = cfg["data"]
    train_cfg = cfg["train"]
    features = pd.read_parquet(data.features_path)
    X = features.drop(columns=[train_cfg.target]).values
    y = features[train_cfg.target].values
    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=train_cfg.test_size, random_state=cfg.seed
    )
    # モデル選択（最小実装：LRのみ）
    model = LogisticRegression(**train_cfg.model.params)
    with mlflow.start_run():
        mlflow.log_params({"model": "LogisticRegression", **train_cfg.model.params})
        model.fit(X_tr, y_tr)
        pred = model.predict(X_te)
        acc = accuracy_score(y_te, pred)
        mlflow.log_metric("accuracy", acc)
        Path(cfg.artifacts_dir).mkdir(exist_ok=True, parents=True)
        out = Path(cfg.artifacts_dir) / "model.joblib"
        joblib.dump(model, out)
        mlflow.log_artifact(str(out))
        print(f"accuracy={acc:.4f}; saved={out}")


if __name__ == "__main__":
    main()

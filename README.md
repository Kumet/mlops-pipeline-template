# MLOps Pipeline Template

最小構成で **学習 → 評価 → モデル保存/登録 → 推論API** まで動くテンプレート。
ローカル完結で始めて、S3/ECR/GPU へ拡張しやすい構成。

## Quick Start
```bash
uv sync --frozen
pre-commit install
uv run dvc init
uv run dvc remote add -d local .dvcstore
uv run dvc repro
docker compose up --build ml-api
# POST /predict に features を投げる
```

## Tech
- Hydra / MLflow / DVC / Prefect / scikit-learn
- FastAPI Serving, Docker, GitHub Actions

## Pipeline (DVC)
- make_dataset → build_features → train → evaluate → (register:将来)
- 生成物: `artifacts/model.joblib`
- MLflow: `./mlruns`（将来 S3 等へ切替）

## Serving
- `src/serving/app.py`（FastAPI）
- `docker compose up --build ml-api` → http://localhost:8001/docs

## CI
- lint → test → dvc repro → docker build
- 将来: GHCR push / tag リリースで MLflow run などを追加

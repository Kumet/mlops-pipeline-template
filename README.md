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

- GPU でサービングする場合は `.env` の `SERVING_FLAVOR=gpu` に変更するか、`SERVING_FLAVOR=gpu docker compose up --build ml-api` を実行してください。
- 直接ビルドする場合: `docker build -f src/serving/Dockerfile --build-arg FLAVOR=gpu -t mlops/serving:gpu .`
- CPU に戻す場合は `SERVING_FLAVOR=cpu` に設定します（デフォルト値）。

- Prefect フローで学習→評価→MLflow 登録→API ロールアウト判定まで自動化できます:
  ```bash
  uv run python flows/train_register_deploy.py
  # 例: GPU サービングイメージもビルドする場合
  uv run python flows/train_register_deploy.py -- --build-image true --flavor gpu --image-name mlops-serving:gpu
  ```

### Developer Experience
- `Makefile` でよく使うタスクをワンライン化しています:
  ```bash
  make install    # uv sync --frozen
  make lint       # Ruff + Black
  make test       # pytest
  make dvc        # dvc repro
  make deploy FLAVOR=gpu IMAGE_NAME=mlops-serving:gpu  # Prefect + Docker build
  ```
- `uvx` を併用しているので、ローカルに Ruff が入っていなくても `make format` で統一フォーマットを適用できます。

## Release Workflow (Template)
- タグ `v*` を push すると `.github/workflows/release-deploy.yml` が起動し、DVC/Prefect の再検証・コンテナビルド・AWS ECR / GCP Cloud Run へのデプロイを **テンプレート** として実行します。
- デフォルトでは `ENABLE_DEPLOY=false` で安全にスキップされます。実際にデプロイしたい場合は以下を実行:
  ```bash
  gh workflow run release-deploy.yml \
    --ref v1.0.0 \
    --field enable_deploy=true \
    --field enable_terraform_apply=true
  ```
- 事前に以下のシークレット設定が必要です（例）:
  - `AWS_DEPLOY_ROLE_ARN` : GitHub Actions から Assume Role するための IAM ロール
  - `AWS_ACCOUNT_ID` : ECR プッシュ時に使用
  - `GCP_SA_KEY` : Cloud Run / Artifact Registry 用サービスアカウント JSON

## Infrastructure as Code (Template)
- `infra/terraform/` 配下に AWS ECR / GCP Cloud Run を構築する Terraform 雛形を追加しています。
- `terraform.tfvars.example` をコピーして各種値を設定すると、以下の手順で計画・適用できます（**デフォルトはローカル backend**）:
  ```bash
  cd infra/terraform
  cp terraform.tfvars.example terraform.tfvars
  terraform init
  terraform plan
  # 実際に構築する場合のみ
  terraform apply
  ```
- GitHub Actions の Terraform ジョブ (`ENABLE_TERRAFORM_APPLY=true`) で CI から `plan/apply` も可能ですが、デフォルトではドライランとなります。

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

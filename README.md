# MLOps Pipeline Template

このリポジトリは、ローカル完結で **データ取得 → 特徴量生成 → 学習 → 評価 → モデル保存 → 推論 API** を構築し、将来的なクラウド展開を見据えたテンプレートです。
Python 3.12 / uv を前提に、Hydra 設定・DVC パイプライン・MLflow ログ・Prefect オーケストレーション・FastAPI サービング・GitHub Actions CI を統合しています。

---

## 主な構成

| 領域 | 使用技術 | 説明 |
| --- | --- | --- |
| 依存管理 | uv | `uv sync --frozen` でロック済み依存を再現 |
| 設定管理 | Hydra | `configs/` にデータ・学習・評価設定を配置 |
| パイプライン | DVC | `dvc.yaml` でデータ→学習→評価の DAG を定義 |
| 実験管理 | MLflow (ローカル) | `./mlruns` に実行履歴を保存。モデルを `artifacts/model.joblib` に出力 |
| オーケストレーション | Prefect | `flows/train_register_deploy.py` で DVC 実行→閾値判定→MLflow 登録→Docker ビルド |
| サービング | FastAPI + Uvicorn | `src/serving/app.py` を Docker (CPU/GPU) で提供可能 |
| CI | GitHub Actions (`ci.yml`) | Lint → Test → DVC repro → Docker build |
| DX | Makefile, uvx | `make lint` や `make deploy` などでタスクをワンライン化 |

---

## クイックスタート

```bash
uv sync --frozen
pre-commit install            # 任意
uv run dvc init               # 初回のみ
uv run dvc remote add -d local .dvcstore  # 任意
make dvc                      # データ生成→学習→評価
docker compose up --build ml-api
```

- GPU サービングは `SERVING_FLAVOR=gpu docker compose up --build ml-api` で実行できます。
- 直接ビルドする場合は `docker build -f src/serving/Dockerfile --build-arg FLAVOR=gpu -t mlops/serving:gpu .` を利用してください。

---

## Makefile コマンド

| コマンド | 内容 |
| --- | --- |
| `make install` / `make sync` | uv sync --frozen |
| `make lint` | Ruff / Black によるチェック |
| `make format` | Black + `uvx ruff format` |
| `make test` | pytest |
| `make dvc` | `uv run dvc repro` |
| `make pipeline` | DVC を再実行 (`--force`) し Prefect フローで登録 |
| `make prefect` | Prefect フローのみ実行 |
| `make deploy FLAVOR=gpu IMAGE_NAME=mlops-serving:gpu` | Prefect + Docker ビルド |

---

## DVC パイプライン

1. `src/data/make_dataset.py` – scikit-learn の Iris を取得し CSV 保存
2. `src/features/build_features.py` – CSV から前処理済み Parquet を生成
3. `src/models/train.py` – Hydra 設定に従いロジスティック回帰を学習し MLflow に記録
4. `src/evaluation/evaluate.py` – 評価指標を算出し `artifacts/metrics.json` に保存・閾値チェック

`make dvc` または `uv run dvc repro` で再現できます。

---

## Prefect フロー

`flows/train_register_deploy.py` は以下を実行します。

1. DVC パイプラインを実行（`force` も指定可能）
2. `artifacts/metrics.json` を読み込み、閾値を満たすか判定
3. MLflow Model Registry に最新モデルを登録
4. `--build-image true` 指定時に Docker イメージをビルド（`FLAVOR` 引数で CPU/GPU 切り替え）

例:
```bash
uv run python flows/train_register_deploy.py
uv run python flows/train_register_deploy.py -- --build-image true --flavor gpu --image-name mlops-serving:gpu
```

---

## サービング

- `src/serving/app.py` が FastAPI エンドポイントを提供します。
  - `GET /health` … ヘルスチェック
  - `POST /predict` … Iris の特徴量を受け取り、予測クラスと最大確率を返却
- モデルファイル `artifacts/model.joblib` を起動時にロードするため、事前に DVC パイプラインを実行してください。
- Dockerfile は `FLAVOR=cpu` (デフォルト) と `FLAVOR=gpu` に対応しています。

---

## CI / Release

- `.github/workflows/ci.yml` は Pull Request / main ブランチへの push で lint, test, dvc repro, docker build を行います。
- `.github/workflows/release-deploy.yml` はタグ `v*` または手動実行で起動する **テンプレート** です。既定ではドライランとして動作し、以下を実施します。
  - DVC パイプラインおよび Prefect フローでの再検証
  - Docker メタデータ生成
  - `enable_deploy=true` を指定した場合のみ AWS ECR / GCP Artifact Registry への push と Cloud Run デプロイ
  - Terraform ジョブは `enable_terraform_apply=true` の時のみ `plan/apply` を実行

手動実行例:
```bash
gh workflow run release-deploy.yml \
  --ref v1.0.0 \
  --field enable_deploy=true \
  --field enable_terraform_apply=true
```

必要なシークレット（例）:
- `AWS_DEPLOY_ROLE_ARN`
- `AWS_ACCOUNT_ID`
- `GCP_SA_KEY`

---

## Terraform テンプレート

`infra/terraform/` には、AWS ECR と GCP Artifact Registry / Cloud Run を構築するサンプルが含まれています。
ローカル backend を利用しており、以下の手順で計画・適用できます。

```bash
cd infra/terraform
cp terraform.tfvars.example terraform.tfvars
terraform init
terraform plan
# 必要に応じて
terraform apply
```

GitHub Actions の Terraform ジョブも同じテンプレートを利用しますが、デフォルト (`enable_terraform_apply=false`) では `plan/apply` がスキップされます。

---

## 技術スタックまとめ

- Python 3.12 / uv
- Hydra / DVC / Prefect / MLflow / scikit-learn
- FastAPI / Uvicorn / Docker / Docker Compose
- GitHub Actions / Terraform (テンプレート)
- Makefile / uvx / pre-commit

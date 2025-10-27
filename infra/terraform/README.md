# Terraform Templates (Placeholder)

このディレクトリは、AWS ECR と GCP Cloud Run/Artifact Registry を利用した
本番デプロイを想定した IaC テンプレートの雛形です。
**実際のデプロイは行われず、各種設定はコメント／変数で無効化されています。**

## 使い方（ローカル）

```bash
cd infra/terraform
cp terraform.tfvars.example terraform.tfvars  # 必要に応じて値を設定
terraform init
terraform plan
# 実際に構築する場合のみ
terraform apply
```

## 前提
- AWS: AssumeRole 可能な IAM ロール、`aws configure` 済み
- GCP: サービスアカウント JSON キー、`gcloud auth application-default login`

## 主なリソース (サンプル)
- AWS
  - ECR リポジトリ
  - IAM ロール（GitHub Actions から推奨）
- GCP
  - Artifact Registry リポジトリ
  - Cloud Run サービス

必要に応じてネットワークリソースや秘密情報の管理 (Secrets Manager / Secret Manager) を追加してください。

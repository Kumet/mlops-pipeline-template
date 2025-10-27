variable "aws_region" {
  description = "AWS region for ECR deployment."
  type        = string
  default     = "us-east-1"
}

variable "aws_ecr_repository" {
  description = "ECR repository name for serving images."
  type        = string
  default     = "mlops-serving"
}

variable "gcp_project" {
  description = "GCP project ID for Artifact Registry / Cloud Run."
  type        = string
  default     = "your-gcp-project"
}

variable "gcp_region" {
  description = "GCP region for Artifact Registry / Cloud Run."
  type        = string
  default     = "us-central1"
}

variable "gcp_registry_repository" {
  description = "GCP Artifact Registry repository ID."
  type        = string
  default     = "mlops"
}

variable "image_name" {
  description = "Container image name (without tag)."
  type        = string
  default     = "mlops-serving"
}

variable "mlflow_tracking_uri" {
  description = "MLflow tracking URI for deployed service."
  type        = string
  default     = "http://localhost:5000"
}

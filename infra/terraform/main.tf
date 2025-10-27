###############################
# AWS ECR (Placeholder)
###############################

resource "aws_ecr_repository" "mlops_serving" {
  name                 = var.aws_ecr_repository
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  lifecycle {
    prevent_destroy = true
  }
}

###############################
# GCP Artifact Registry & Cloud Run (Placeholder)
###############################

resource "google_artifact_registry_repository" "mlops" {
  location      = var.gcp_region
  repository_id = var.gcp_registry_repository
  description   = "Container images for MLOps serving"
  format        = "DOCKER"
}

resource "google_service_account" "cloud_run" {
  account_id   = "mlops-cloud-run"
  display_name = "MLOps Cloud Run Service Account"
}

resource "google_cloud_run_service" "mlops_api" {
  name     = "mlops-serving-api"
  location = var.gcp_region

  template {
    spec {
      containers {
        image = "${var.gcp_region}-docker.pkg.dev/${var.gcp_project}/${var.gcp_registry_repository}/${var.image_name}:latest"
        env {
          name  = "MLFLOW_TRACKING_URI"
          value = var.mlflow_tracking_uri
        }
      }
      service_account_name = google_service_account.cloud_run.email
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

  autogenerate_revision_name = true

  lifecycle {
    prevent_destroy = true
  }
}

###############################
# Outputs
###############################

output "aws_ecr_repository_url" {
  value       = aws_ecr_repository.mlops_serving.repository_url
  description = "ECR repository URL where the serving image should be pushed."
}

output "cloud_run_url" {
  value       = google_cloud_run_service.mlops_api.status[0].url
  description = "URL of the Cloud Run service (if deployed)."
}

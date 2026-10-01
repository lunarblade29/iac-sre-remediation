terraform {
  required_version = ">= 1.5.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }

  # In production, we configure a remote GCS backend for state locking:
  # backend "gcs" {
  #   bucket  = "YOUR_TERRAFORM_STATE_BUCKET"
  #   prefix  = "terraform/state"
  # }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# 1. Enable required APIs automatically
resource "google_project_service" "run_api" {
  service            = "run.googleapis.com"
  disable_on_destroy = false
}

# 2. Define the Cloud Run Service
resource "google_cloud_run_v2_service" "app_service" {
  name     = var.service_name
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    scaling {
      min_instance_count = 1 # Keep 1 warm instance so health checks never time out
      max_instance_count = 3 # Cap it to avoid unexpected costs
    }

    containers {
      image = var.image_url

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
      }

      ports {
        container_port = 8080
      }

      # SRE Health Check (Liveness Probe)
      liveness_probe {
        http_get {
          path = "/"
          port = 8080
        }
        initial_delay_seconds = 5
        period_seconds        = 10
        failure_threshold     = 3
      }
    }
  }

  depends_on = [google_project_service.run_api]
}

# 3. Allow unauthenticated public access (so we and our monitor can query it)
resource "google_cloud_run_v2_service_iam_member" "public_access" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.app_service.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
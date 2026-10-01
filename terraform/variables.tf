variable "project_id" {
  description = "The Google Cloud Project ID"
  type        = string
}

variable "region" {
  description = "Google Cloud Region for resources"
  type        = string
  default     = "europe-west1" # Dublin/Europe region, or use us-central1
}

variable "service_name" {
  description = "The name of the Cloud Run service"
  type        = string
  default     = "sre-resilient-service"
}

variable "image_url" {
  description = "The Docker container image to deploy"
  type        = string
  default     = "gcr.io/cloudrun/hello" # Placeholder until our CI/CD pipeline builds our custom image
}
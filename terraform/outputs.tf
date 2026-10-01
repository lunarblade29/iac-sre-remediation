output "service_url" {
  description = "The public URL of the deployed Cloud Run service"
  value       = google_cloud_run_v2_service.app_service.uri
}

output "service_name" {
  description = "The name of the service"
  value       = google_cloud_run_v2_service.app_service.name
}
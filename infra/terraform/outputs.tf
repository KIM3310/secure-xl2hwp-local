output "service_url" {
  description = "Cloud Run URL."
  value       = google_cloud_run_v2_service.secure_xl2hwp_local.uri
}

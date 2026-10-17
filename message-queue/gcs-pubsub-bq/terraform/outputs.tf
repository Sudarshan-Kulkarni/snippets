output "bucket_name" {
  description = "Name of the GCS bucket for PDF uploads"
  value       = google_storage_bucket.pdf_bucket.name
}

output "upload_topic_name" {
  description = "Stage 1 Pub/Sub topic receiving GCS notifications"
  value       = google_pubsub_topic.pdf_uploaded.name
}

output "parser_function_uri" {
  description = "HTTPS push URI of the Stage 2 PDF Parser Cloud Function"
  value       = google_cloudfunctions2_function.pdf_parser.service_config[0].uri
}

output "parsed_topic_name" {
  description = "Stage 2 Pub/Sub topic receiving parsed PDF text"
  value       = google_pubsub_topic.pdf_parsed.name
}

output "summarizer_function_uri" {
  description = "HTTPS push URI of the Stage 3 PDF Summarizer Cloud Function"
  value       = google_cloudfunctions2_function.pdf_summarizer.service_config[0].uri
}

output "bigquery_parsed_table" {
  description = "Full BigQuery table reference for parsed PDFs and summaries"
  value       = "${var.project_id}.${google_bigquery_dataset.pdf_pipeline.dataset_id}.${google_bigquery_table.parsed_documents.table_id}"
}

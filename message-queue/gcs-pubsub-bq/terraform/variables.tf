variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP region (us-central1, us-east1, or us-west1 for GCS Always Free tier)"
  type        = string
  default     = "us-central1"
}

variable "upload_topic_id" {
  description = "Stage 1 Pub/Sub topic that receives GCS OBJECT_FINALIZE notifications"
  type        = string
  default     = "pdf-uploaded"
}

variable "parsed_topic_id" {
  description = "Stage 2 Pub/Sub topic that receives parsed PDF text for LLM summarization"
  type        = string
  default     = "pdf-parsed"
}

variable "parsed_subscription_id" {
  description = "Stage 2 Pub/Sub subscription for inspecting / consuming parsed PDF events"
  type        = string
  default     = "pdf-parsed-sub"
}

variable "bq_dataset_id" {
  description = "BigQuery dataset ID for storing parsed PDFs and summaries"
  type        = string
  default     = "pdf_pipeline"
}

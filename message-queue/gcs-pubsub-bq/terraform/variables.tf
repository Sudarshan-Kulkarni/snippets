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

variable "bq_dataset_id" {
  description = "BigQuery dataset ID for storing parsed PDFs and summaries"
  type        = string
  default     = "pdf_pipeline"
}

variable "gemini_api_key" {
  description = "Google AI Studio API key for Gemini summarization"
  type        = string
  sensitive   = true
}

variable "gemini_model" {
  description = "Gemini model ID used by the summarizer function"
  type        = string
  default     = "gemini-3.8-flash"
}

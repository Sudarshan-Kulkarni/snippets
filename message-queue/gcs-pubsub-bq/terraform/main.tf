terraform {
  required_version = ">= 1.3.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.4"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# 1. Enable required GCP APIs (kept enabled on destroy so other snippets aren't affected)
locals {
  apis = [
    "storage.googleapis.com",
    "pubsub.googleapis.com",
    "bigquery.googleapis.com",
    "cloudfunctions.googleapis.com",
    "run.googleapis.com",
    "cloudbuild.googleapis.com",
    "artifactregistry.googleapis.com",
    "eventarc.googleapis.com",
  ]
}

resource "google_project_service" "apis" {
  for_each           = toset(local.apis)
  service            = each.value
  disable_on_destroy = false
}

# 2. GCS Bucket for incoming PDFs (us-central1 + STANDARD qualifies for Always Free 5 GB/month)
resource "google_storage_bucket" "pdf_bucket" {
  name                        = "${var.project_id}-pdf-ingest"
  location                    = var.region
  storage_class               = "STANDARD"
  uniform_bucket_level_access = true
  force_destroy               = true

  depends_on = [google_project_service.apis["storage.googleapis.com"]]
}

# Separate bucket to hold Cloud Function source zip archives (so uploading source zips
# doesn't trigger the PDF ingest bucket's OBJECT_FINALIZE notification)
resource "google_storage_bucket" "fn_source_bucket" {
  name                        = "${var.project_id}-fn-source"
  location                    = var.region
  storage_class               = "STANDARD"
  uniform_bucket_level_access = true
  force_destroy               = true

  depends_on = [google_project_service.apis["storage.googleapis.com"]]
}

# 3. Stage 1 Pub/Sub Topic (receives GCS upload events; Eventarc creates the Push Subscription)
resource "google_pubsub_topic" "pdf_uploaded" {
  name       = var.upload_topic_id
  depends_on = [google_project_service.apis["pubsub.googleapis.com"]]
}

# 4. Grant the project's built-in Cloud Storage Service Agent permission to publish to Topic 1
data "google_storage_project_service_account" "gcs_account" {
  depends_on = [google_project_service.apis["storage.googleapis.com"]]
}

resource "google_pubsub_topic_iam_member" "gcs_publisher" {
  topic  = google_pubsub_topic.pdf_uploaded.id
  role   = "roles/pubsub.publisher"
  member = "serviceAccount:${data.google_storage_project_service_account.gcs_account.email_address}"
}

# 5. Wire the GCS Bucket to publish an event to Topic 1 whenever an upload finishes (OBJECT_FINALIZE)
resource "google_storage_notification" "pdf_upload_notification" {
  bucket         = google_storage_bucket.pdf_bucket.name
  payload_format = "JSON_API_V1"
  topic          = google_pubsub_topic.pdf_uploaded.id
  event_types    = ["OBJECT_FINALIZE"]

  depends_on = [google_pubsub_topic_iam_member.gcs_publisher]
}

# 6. Stage 2 Pub/Sub Topic (receives parsed PDF events; Eventarc creates the Push Subscription)
resource "google_pubsub_topic" "pdf_parsed" {
  name       = var.parsed_topic_id
  depends_on = [google_project_service.apis["pubsub.googleapis.com"]]
}

# 7. BigQuery Dataset & Table for raw parsed PDF contents + LLM summary
resource "google_bigquery_dataset" "pdf_pipeline" {
  dataset_id                 = var.bq_dataset_id
  location                   = var.region
  delete_contents_on_destroy = true

  depends_on = [google_project_service.apis["bigquery.googleapis.com"]]
}

resource "google_bigquery_table" "parsed_documents" {
  dataset_id          = google_bigquery_dataset.pdf_pipeline.dataset_id
  table_id            = "parsed_documents"
  deletion_protection = false

  schema = jsonencode([
    { name = "doc_id", type = "STRING", mode = "REQUIRED" },
    { name = "bucket", type = "STRING", mode = "REQUIRED" },
    { name = "object_name", type = "STRING", mode = "REQUIRED" },
    { name = "generation", type = "STRING", mode = "NULLABLE" },
    { name = "page_count", type = "INT64", mode = "REQUIRED" },
    { name = "char_count", type = "INT64", mode = "REQUIRED" },
    { name = "raw_text", type = "STRING", mode = "REQUIRED" },
    { name = "parsed_at", type = "TIMESTAMP", mode = "REQUIRED" },
    { name = "summary", type = "STRING", mode = "NULLABLE" },
    { name = "summarized_at", type = "TIMESTAMP", mode = "NULLABLE" },
  ])
}

# 8. Cloud Build permissions for the default Compute Engine service account
data "google_project" "current" {}

locals {
  build_sa_roles = [
    "roles/cloudbuild.builds.builder",
    "roles/logging.logWriter",
    "roles/artifactregistry.writer",
    "roles/storage.objectViewer",
  ]
}

resource "google_project_iam_member" "build_sa_permissions" {
  for_each = toset(local.build_sa_roles)
  project  = var.project_id
  role     = each.value
  member   = "serviceAccount:${data.google_project.current.number}-compute@developer.gserviceaccount.com"
}

# 9. Stage 2: Least-Privilege Service Account & Cloud Function (PDF Parser)
resource "google_service_account" "parser_sa" {
  account_id   = "pdf-parser-fn-sa"
  display_name = "PDF Parser Cloud Function Service Account"
}

resource "google_storage_bucket_iam_member" "parser_bucket_viewer" {
  bucket = google_storage_bucket.pdf_bucket.name
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${google_service_account.parser_sa.email}"
}

resource "google_bigquery_dataset_iam_member" "parser_bq_editor" {
  dataset_id = google_bigquery_dataset.pdf_pipeline.dataset_id
  role       = "roles/bigquery.dataEditor"
  member     = "serviceAccount:${google_service_account.parser_sa.email}"
}

resource "google_project_iam_member" "parser_bq_job_user" {
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_service_account.parser_sa.email}"
}

resource "google_pubsub_topic_iam_member" "parser_pubsub_publisher" {
  topic  = google_pubsub_topic.pdf_parsed.id
  role   = "roles/pubsub.publisher"
  member = "serviceAccount:${google_service_account.parser_sa.email}"
}

data "archive_file" "parser_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../functions/parser"
  output_path = "${path.module}/parser-source.zip"
}

resource "google_storage_bucket_object" "parser_zip_object" {
  name   = "parser-${data.archive_file.parser_zip.output_md5}.zip"
  bucket = google_storage_bucket.fn_source_bucket.name
  source = data.archive_file.parser_zip.output_path
}

resource "google_cloudfunctions2_function" "pdf_parser" {
  name        = "pdf-parser"
  location    = var.region
  description = "Parses uploaded PDFs from GCS, loads raw text into BigQuery, and publishes to pdf-parsed"

  build_config {
    runtime     = "python312"
    entry_point = "parse_pdf_event"
    source {
      storage_source {
        bucket = google_storage_bucket.fn_source_bucket.name
        object = google_storage_bucket_object.parser_zip_object.name
      }
    }
  }

  service_config {
    min_instance_count    = 0
    max_instance_count    = 1
    available_memory      = "512M"
    timeout_seconds       = 60
    service_account_email = google_service_account.parser_sa.email

    environment_variables = {
      GCP_PROJECT_ID         = var.project_id
      PUBSUB_PARSED_TOPIC_ID = google_pubsub_topic.pdf_parsed.name
      BQ_DATASET_ID          = google_bigquery_dataset.pdf_pipeline.dataset_id
      BQ_PARSED_TABLE_ID     = google_bigquery_table.parsed_documents.table_id
    }
  }

  event_trigger {
    trigger_region        = var.region
    event_type            = "google.cloud.pubsub.topic.v1.messagePublished"
    pubsub_topic          = google_pubsub_topic.pdf_uploaded.id
    retry_policy          = "RETRY_POLICY_RETRY"
    service_account_email = google_service_account.parser_sa.email
  }

  depends_on = [
    google_project_service.apis["cloudfunctions.googleapis.com"],
    google_project_service.apis["run.googleapis.com"],
    google_project_service.apis["cloudbuild.googleapis.com"],
    google_project_service.apis["artifactregistry.googleapis.com"],
    google_project_service.apis["eventarc.googleapis.com"],
    google_project_iam_member.build_sa_permissions,
    google_storage_bucket_iam_member.parser_bucket_viewer,
    google_bigquery_dataset_iam_member.parser_bq_editor,
    google_project_iam_member.parser_bq_job_user,
    google_pubsub_topic_iam_member.parser_pubsub_publisher,
  ]
}

resource "google_cloud_run_service_iam_member" "parser_invoker" {
  location = google_cloudfunctions2_function.pdf_parser.location
  service  = google_cloudfunctions2_function.pdf_parser.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.parser_sa.email}"
}

# 10. Stage 3: Least-Privilege Service Account & Cloud Function (Gemini Summarizer)
resource "google_service_account" "summarizer_sa" {
  account_id   = "pdf-summarizer-fn-sa"
  display_name = "PDF Summarizer Cloud Function Service Account"
}

resource "google_bigquery_dataset_iam_member" "summarizer_bq_editor" {
  dataset_id = google_bigquery_dataset.pdf_pipeline.dataset_id
  role       = "roles/bigquery.dataEditor"
  member     = "serviceAccount:${google_service_account.summarizer_sa.email}"
}

resource "google_project_iam_member" "summarizer_bq_job_user" {
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_service_account.summarizer_sa.email}"
}

data "archive_file" "summarizer_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../functions/summarizer"
  output_path = "${path.module}/summarizer-source.zip"
}

resource "google_storage_bucket_object" "summarizer_zip_object" {
  name   = "summarizer-${data.archive_file.summarizer_zip.output_md5}.zip"
  bucket = google_storage_bucket.fn_source_bucket.name
  source = data.archive_file.summarizer_zip.output_path
}

resource "google_cloudfunctions2_function" "pdf_summarizer" {
  name        = "pdf-summarizer"
  location    = var.region
  description = "Summarizes parsed PDF text with Gemini and updates the BigQuery row"

  build_config {
    runtime     = "python312"
    entry_point = "summarize_pdf_event"
    source {
      storage_source {
        bucket = google_storage_bucket.fn_source_bucket.name
        object = google_storage_bucket_object.summarizer_zip_object.name
      }
    }
  }

  service_config {
    min_instance_count    = 0
    max_instance_count    = 1
    available_memory      = "512M"
    timeout_seconds       = 120
    service_account_email = google_service_account.summarizer_sa.email

    environment_variables = {
      GCP_PROJECT_ID     = var.project_id
      BQ_DATASET_ID      = google_bigquery_dataset.pdf_pipeline.dataset_id
      BQ_PARSED_TABLE_ID = google_bigquery_table.parsed_documents.table_id
      GEMINI_API_KEY     = var.gemini_api_key
      GEMINI_MODEL       = var.gemini_model
    }
  }

  event_trigger {
    trigger_region        = var.region
    event_type            = "google.cloud.pubsub.topic.v1.messagePublished"
    pubsub_topic          = google_pubsub_topic.pdf_parsed.id
    retry_policy          = "RETRY_POLICY_RETRY"
    service_account_email = google_service_account.summarizer_sa.email
  }

  depends_on = [
    google_project_service.apis["cloudfunctions.googleapis.com"],
    google_project_service.apis["run.googleapis.com"],
    google_project_service.apis["cloudbuild.googleapis.com"],
    google_project_service.apis["artifactregistry.googleapis.com"],
    google_project_service.apis["eventarc.googleapis.com"],
    google_project_iam_member.build_sa_permissions,
    google_bigquery_dataset_iam_member.summarizer_bq_editor,
    google_project_iam_member.summarizer_bq_job_user,
  ]
}

resource "google_cloud_run_service_iam_member" "summarizer_invoker" {
  location = google_cloudfunctions2_function.pdf_summarizer.location
  service  = google_cloudfunctions2_function.pdf_summarizer.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.summarizer_sa.email}"
}

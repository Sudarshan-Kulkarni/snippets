"""Cloud Function (2nd Gen): Triggered via Pub/Sub push when a PDF is uploaded to GCS.
Downloads the PDF, extracts text with PyMuPDF, loads raw text into BigQuery,
and publishes the extracted text to the Pub/Sub topic for LLM summarization.
"""
import base64
from datetime import datetime, timezone
import json
import os
from typing import Tuple

from cloudevents.http import CloudEvent
import fitz  # PyMuPDF
import functions_framework
from google.cloud import bigquery, pubsub_v1, storage

PROJECT_ID = os.environ["GCP_PROJECT_ID"]
PARSED_TOPIC_ID = os.environ.get("PUBSUB_PARSED_TOPIC_ID", "pdf-parsed")
BQ_DATASET_ID = os.environ.get("BQ_DATASET_ID", "pdf_pipeline")
BQ_PARSED_TABLE_ID = os.environ.get("BQ_PARSED_TABLE_ID", "parsed_documents")

# Reuse clients across warm function invocations
storage_client = storage.Client(project=PROJECT_ID)
bq_client = bigquery.Client(project=PROJECT_ID)
publisher = pubsub_v1.PublisherClient()


def extract_pdf_text(pdf_bytes: bytes) -> Tuple[int, str]:
    """Extract page count and concatenated plain text from PDF bytes in memory."""
    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
        pages = [page.get_text("text") for page in doc]
        return len(pages), "\n".join(pages).strip()


@functions_framework.cloud_event
def parse_pdf_event(cloud_event: CloudEvent) -> None:
    """Handle one Pub/Sub push CloudEvent containing a GCS OBJECT_FINALIZE payload.

    Returning normally responds with HTTP 200 OK (Pub/Sub acks the message).
    Raising an exception responds with HTTP 500 (Pub/Sub nacks and retries).
    """
    pubsub_message = cloud_event.data.get("message", {})
    raw_data = base64.b64decode(pubsub_message.get("data", "")).decode("utf-8")
    event = json.loads(raw_data)

    bucket_name = event["bucket"]
    object_name = event["name"]
    generation = str(event.get("generation", ""))

    if not object_name.lower().endswith(".pdf"):
        print(f"Skipping non-PDF object: gs://{bucket_name}/{object_name}")
        return

    print(f"Downloading gs://{bucket_name}/{object_name} ...")
    blob = storage_client.bucket(bucket_name).blob(object_name)
    pdf_bytes = blob.download_as_bytes()

    page_count, raw_text = extract_pdf_text(pdf_bytes)
    doc_id = f"{bucket_name}/{object_name}#{generation}"
    now_iso = datetime.now(timezone.utc).isoformat()

    row = {
        "doc_id": doc_id,
        "bucket": bucket_name,
        "object_name": object_name,
        "generation": generation,
        "page_count": page_count,
        "char_count": len(raw_text),
        "raw_text": raw_text,
        "parsed_at": now_iso,
    }

    # Batch Load job (load_table_from_json) is 100% free on BigQuery's Always Free tier
    table_ref = f"{PROJECT_ID}.{BQ_DATASET_ID}.{BQ_PARSED_TABLE_ID}"
    load_job = bq_client.load_table_from_json([row], table_ref)
    load_job.result()
    print(
        f"Loaded into BigQuery ({table_ref}): doc_id={doc_id} "
        f"pages={page_count} chars={len(raw_text)}"
    )

    # Publish extracted text to Topic 2 for the LLM Summarizer stage
    next_event = json.dumps(
        {
            "doc_id": doc_id,
            "bucket": bucket_name,
            "object_name": object_name,
            "page_count": page_count,
            "raw_text": raw_text,
            "parsed_at": now_iso,
        }
    ).encode("utf-8")
    topic_path = publisher.topic_path(PROJECT_ID, PARSED_TOPIC_ID)
    published_id = publisher.publish(
        topic_path, next_event, source="pdf-parser-fn"
    ).result()
    print(f"Published to {PARSED_TOPIC_ID}: message_id={published_id}")

"""Cloud Function: Triggered via Pub/Sub push when a parsed PDF event
arrives on `pdf-parsed`. Summarizes the extracted text with Gemini (`gemini-3.8-flash`)
and updates the row in BigQuery.
"""
import base64
import json
import os

from cloudevents.http import CloudEvent
import functions_framework
from google import genai
from google.cloud import bigquery

PROJECT_ID = os.environ["GCP_PROJECT_ID"]
BQ_DATASET_ID = os.environ.get("BQ_DATASET_ID", "pdf_pipeline")
BQ_PARSED_TABLE_ID = os.environ.get("BQ_PARSED_TABLE_ID", "parsed_documents")
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.8-flash")

# Reuse clients across warm function invocations
bq_client = bigquery.Client(project=PROJECT_ID)
genai_client = genai.Client(api_key=GEMINI_API_KEY)


@functions_framework.cloud_event
def summarize_pdf_event(cloud_event: CloudEvent) -> None:
    """Handle one Pub/Sub push CloudEvent from `pdf-parsed`."""
    pubsub_message = cloud_event.data.get("message", {})
    raw_data = base64.b64decode(pubsub_message.get("data", "")).decode("utf-8")
    event = json.loads(raw_data)

    doc_id = event["doc_id"]
    object_name = event.get("object_name", doc_id)
    raw_text = (event.get("raw_text") or "").strip()

    if not raw_text:
        print(f"Skipping summarization for {doc_id}: raw_text is empty")
        return

    print(f"Summarizing {doc_id} ({len(raw_text)} chars) with {GEMINI_MODEL} ...")
    prompt = (
        f"Provide a clear, concise summary of the following PDF document "
        f"({object_name}):\n\n{raw_text}"
    )
    response = genai_client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
    )
    summary_text = (response.text or "").strip()

    table_ref = f"{PROJECT_ID}.{BQ_DATASET_ID}.{BQ_PARSED_TABLE_ID}"
    query = f"""
        UPDATE `{table_ref}`
        SET summary = @summary,
            summarized_at = CURRENT_TIMESTAMP()
        WHERE doc_id = @doc_id
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("summary", "STRING", summary_text),
            bigquery.ScalarQueryParameter("doc_id", "STRING", doc_id),
        ]
    )
    bq_client.query(query, job_config=job_config).result()
    print(f"Updated BigQuery row for {doc_id} with summary ({len(summary_text)} chars)")

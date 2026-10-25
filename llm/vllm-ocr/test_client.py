import argparse
import base64
import os
from pathlib import Path
from openai import OpenAI

# Helper to load .env without external dependencies
env_file = Path(__file__).parent / ".env"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def encode_image(image_path: str) -> str:
    """Encodes an image file to a base64 data URI string."""
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image not found at path: {image_path}")

    suffix = path.suffix.lower()
    mime_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
    }
    mime_type = mime_types.get(suffix, "image/jpeg")

    with open(path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")
    return f"data:{mime_type};base64,{encoded}"


def run_ocr(endpoint_url: str, image_path: str, prompt: str = "ocr"):
    """Sends the image and task prompt to the vLLM OpenAI-compatible endpoint."""
    base_url = endpoint_url.rstrip("/")
    if not base_url.endswith("/v1"):
        base_url = f"{base_url}/v1"

    client = OpenAI(base_url=base_url, api_key="dummy-key")
    image_uri = encode_image(image_path)

    print(f"Connecting to: {base_url}")
    print(f"Image: {image_path}")
    print(f"Prompt: '{prompt}'")
    print("Waiting for OCR response...")

    response = client.chat.completions.create(
        model="google/paligemma2-3b-mix-448",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": image_uri}},
                ],
            }
        ],
        max_tokens=256,
        temperature=0.0,
    )

    print("\n" + "=" * 40)
    print("OCR RESULT:")
    print("=" * 40)
    print(response.choices[0].message.content)
    print("=" * 40)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test vLLM PaliGemma OCR endpoint")
    default_url = os.getenv("MODAL_ENDPOINT_URL")
    parser.add_argument(
        "--url",
        required=not bool(default_url),
        default=default_url,
        help="Modal web server URL (default: read from MODAL_ENDPOINT_URL in .env)",
    )
    parser.add_argument(
        "--image",
        required=True,
        help="Path to the image to perform OCR on (e.g. sample.jpg)",
    )
    parser.add_argument(
        "--prompt",
        default="ocr",
        help="Task prompt (default: 'ocr', can also use 'read license plate' or 'detect text')",
    )

    args = parser.parse_args()
    run_ocr(endpoint_url=args.url, image_path=args.image, prompt=args.prompt)

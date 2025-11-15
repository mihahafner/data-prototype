# tools/s3_publish.py
from __future__ import annotations
import hashlib
import os
from pathlib import Path
import webbrowser

import boto3
from botocore.exceptions import ClientError
import requests

THIS_FILE = Path(__file__).resolve()
REPO_ROOT = THIS_FILE.parents[1]
DATA_DIR  = REPO_ROOT / "data"
PROCESSED = DATA_DIR / "processed"

BUCKET = "mihah-weather-data"
REGION = "eu-north-1"

LOCAL = PROCESSED / "weather_lju_anomalies.csv"
KEY = "processed/weather_lju_anomalies.csv"

def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()[:12]

def ensure_aws_profile_info():
    print("AWS profile info:")
    print(" - AWS_DEFAULT_REGION:", os.environ.get("AWS_DEFAULT_REGION"))
    print(" - AWS_REGION        :", os.environ.get("AWS_REGION"))
    print(" - Using boto3 region:", REGION)
    print("Local paths:")
    print(" - REPO_ROOT         :", REPO_ROOT)
    print(" - LOCAL             :", LOCAL)

def upload_public_csv(local: Path, bucket: str, key: str, region: str) -> str:
    if not local.exists():
        raise FileNotFoundError(f"Local file not found: {local}")

    s3 = boto3.client("s3", region_name=region)

    data = local.read_bytes()
    sha = sha256_bytes(data)
    print(f"Uploading {local} ({len(data)} bytes, sha256:{sha}) → s3://{bucket}/{key}")

    try:
        s3.put_object(
            Bucket=bucket,
            Key=key,
            Body=data,
            ContentType="text/csv; charset=utf-8",
            CacheControl="no-cache"
            # No ACL here—bucket policy provides public read
        )
    except ClientError as e:
        raise SystemExit(f"Upload failed: {e}")

    head = s3.head_object(Bucket=bucket, Key=key)
    print("S3 HEAD:",
          "\n - ContentType :", head.get("ContentType"),
          "\n - Size        :", head.get("ContentLength"),
          "\n - ETag        :", head.get("ETag"))

    url = f"https://{bucket}.s3.{region}.amazonaws.com/{key}"
    print("Public URL:", url)
    return url

def verify_public(url: str, want_snippet: int = 120) -> None:
    print("Verifying public accessibility…")
    r = requests.get(url, timeout=15)
    r.raise_for_status()
    print(f"HTTP {r.status_code}, {len(r.content)} bytes")
    print("First bytes:\n", r.content[:want_snippet].decode("utf-8", errors="replace"))

def open_in_browser(url: str):
    try:
        webbrowser.open(url)
        print("Opened in default browser.")
    except Exception:
        print("Could not open browser automatically. Copy this URL:\n", url)

def main():
    ensure_aws_profile_info()
    url = upload_public_csv(LOCAL, BUCKET, KEY, REGION)
    verify_public(url)
    open_in_browser(url)

if __name__ == "__main__":
    main()

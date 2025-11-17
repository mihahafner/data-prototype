from __future__ import annotations
from pathlib import Path
import time, sqlite3
import pandas as pd
import requests
import boto3
from sklearn.ensemble import IsolationForest

# ---------- Config ----------
BUCKET   = "mihah-weather-data"
REGION   = "eu-north-1"
KEY      = "processed/weather_lju_anomalies.csv"

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR  = REPO_ROOT / "data"
RAW_DIR   = DATA_DIR / "raw"
PROC_DIR  = DATA_DIR / "processed"
DB_PATH   = DATA_DIR / "proto.db"
RAW_CSV   = RAW_DIR / "weather_lju.csv"
PROC_CSV  = PROC_DIR / "weather_lju_anomalies.csv"

API_URL = "https://api.open-meteo.com/v1/forecast"
PARAMS = {
    "latitude": 46.05,
    "longitude": 14.51,
    "hourly": "temperature_2m,relativehumidity_2m",
}

RAW_DIR.mkdir(parents=True, exist_ok=True)
PROC_DIR.mkdir(parents=True, exist_ok=True)

def fetch_with_retry(url, params, retries=4, base_delay=2):
    last = None
    for i in range(retries):
        try:
            r = requests.get(url, params=params, timeout=15)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            last = e
            time.sleep(base_delay * (i + 1))
    raise RuntimeError(f"API fetch failed after retries: {last}")

def upload_no_acl(local: Path, bucket: str, key: str, region: str) -> str:
    s3 = boto3.client("s3", region_name=region)
    with open(local, "rb") as f:
        s3.put_object(
            Bucket=bucket,
            Key=key,
            Body=f,
            ContentType="text/csv; charset=utf-8",
            CacheControl="no-cache",
        )
    s3.head_object(Bucket=bucket, Key=key)
    return f"https://{bucket}.s3.{region}.amazonaws.com/{key}"

def main():
    # 1) API -> CSV
    try:
        payload = fetch_with_retry(API_URL, PARAMS)
        df_raw = pd.DataFrame({
            "time": payload["hourly"]["time"],
            "temp": payload["hourly"]["temperature_2m"],
            "humidity": payload["hourly"]["relativehumidity_2m"],
        })
        df_raw.to_csv(RAW_CSV, index=False)
        print(f"Saved: {RAW_CSV}")
    except Exception as e:
        if RAW_CSV.exists():
            print(f"⚠️ Using cached raw CSV ({e})")
            df_raw = pd.read_csv(RAW_CSV)
        else:
            raise

    # 2) Load -> SQLite
    conn = sqlite3.connect(DB_PATH)
    df_raw.to_sql("weather_lju", conn, if_exists="replace", index=False)
    print(f"Wrote table to {DB_PATH}")

    # 3) Anomalies
    df = pd.read_sql("SELECT * FROM weather_lju", conn)
    conn.close()
    df["temp"] = pd.to_numeric(df["temp"], errors="coerce")
    df["humidity"] = pd.to_numeric(df["humidity"], errors="coerce")
    df = df.dropna(subset=["temp"])
    model = IsolationForest(contamination=0.05, random_state=42)
    df["is_anomaly"] = model.fit_predict(df[["temp"]])
    df.to_csv(PROC_CSV, index=False)
    print(f"Saved: {PROC_CSV}")

    # 4) Upload (NO ACL)
    url = upload_no_acl(PROC_CSV, BUCKET, KEY, REGION)
    print("Public URL:", url)

    # 5) Verify
    try:
        r = requests.get(url, timeout=15)
        print("Verify GET:", r.status_code, "-", "OK" if r.ok else "FAIL")
    except Exception as e:
        print("Verify GET failed:", e)

    # 6) Summary
    print("\n=== SUMMARY ===")
    print(df.describe())
    print("\nCounts:", df["is_anomaly"].value_counts().to_dict())
    print("\n✅ Done.")

if __name__ == "__main__":
    main()

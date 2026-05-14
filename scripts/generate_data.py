import json
import uuid
import random
import boto3
from datetime import datetime, timedelta

RAW_BUCKET = "sample-dwh-raw-zone"  # terraform apply で作成されたバケット名
s3 = boto3.client("s3", region_name="ap-northeast-1")

# --- 売上データ生成（24時間分、1時間ごと） ---
stores = ["Store A", "Store B", "Store C"]
scales = ["yen", "us_dollar"]
sales_records = []

base_time = datetime.now().replace(minute=0, second=0, microsecond=0)
for i in range(24):
    t = base_time - timedelta(hours=i)
    for store in stores:
        sales_records.append({
            "purchase_id": str(uuid.uuid4()),
            "store_name": store,
            "sales": round(random.uniform(1000, 50000), 2),
            "scale": random.choice(scales),
            "time": t.isoformat()
        })

sales_json = "\n".join(json.dumps(r) for r in sales_records)
date_str = base_time.strftime("%Y/%m/%d")

s3.put_object(
    Bucket=RAW_BUCKET,
    Key=f"sales/{date_str}/sales_{base_time.strftime('%H%M%S')}.json",
    Body=sales_json
)
print(f"Uploaded {len(sales_records)} sales records")

# --- 為替データ生成（本日分） ---
currency_data = {"currency": "JPY", "rates": round(random.uniform(140, 160), 2)}
s3.put_object(
    Bucket=RAW_BUCKET,
    Key=f"currency/{date_str}/rates.json",
    Body=json.dumps(currency_data)
)
print(f"Uploaded currency rate: 1 USD = {currency_data['rates']} JPY")

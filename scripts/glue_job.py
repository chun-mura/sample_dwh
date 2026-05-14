import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql import functions as F
from pyspark.sql.functions import col, when, to_date

args = getResolvedOptions(sys.argv, ["JOB_NAME", "RAW_BUCKET", "GOLD_BUCKET"])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args["JOB_NAME"], args)

RAW_BUCKET  = args["RAW_BUCKET"]
GOLD_BUCKET = args["GOLD_BUCKET"]

# --- 1. データ読み込み ---
sales_df    = spark.read.option("recursiveFileLookup", "true").json(f"s3://{RAW_BUCKET}/sales/")
currency_df = spark.read.option("recursiveFileLookup", "true").json(f"s3://{RAW_BUCKET}/currency/")

# --- 2. データ品質テスト: purchase_idの重複チェック ---
duplicate_count = sales_df.groupBy("purchase_id").count().filter(col("count") > 1).count()
if duplicate_count > 0:
    raise Exception(f"Data quality error: {duplicate_count} duplicate purchase_id(s) found")

# --- 3. 為替レートを結合して円換算 ---
usd_rate = currency_df.filter(col("currency") == "JPY").select("rates").first()["rates"]

sales_df = sales_df.withColumn(
    "sales_jpy",
    when(col("scale") == "us_dollar", col("sales") * usd_rate)
    .otherwise(col("sales"))
)

# --- 4. 日付カラムを追加（パーティション用）---
sales_df = sales_df.withColumn("date", to_date(col("time"))) \
                   .withColumn("store", col("store_name"))

# --- 5. Parquet形式でGold Zoneに書き込み（パーティション分割）---
sales_df.write \
    .mode("append") \
    .partitionBy("date", "store") \
    .parquet(f"s3://{GOLD_BUCKET}/sales/")

job.commit()

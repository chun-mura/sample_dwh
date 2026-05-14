CREATE EXTERNAL TABLE IF NOT EXISTS sample_dwh.sales (
    purchase_id STRING,
    store_name  STRING,
    sales       DOUBLE,
    scale       STRING,
    time        STRING,
    sales_jpy   DOUBLE
)
PARTITIONED BY (
    date  STRING,
    store STRING
)
STORED AS PARQUET
LOCATION 's3://sample-dwh-gold-zone/sales/'
TBLPROPERTIES ('parquet.compress' = 'SNAPPY');

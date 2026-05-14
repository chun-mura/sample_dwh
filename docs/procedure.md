# データ分析基盤 構築手順書

## 概要

売上データの可視化プロジェクトとして、AWSを使った4レイヤー構成のデータ分析基盤を構築する。

```
売上API(モック) ─┐
                  ├─→ S3 Raw Zone → Glue(加工) → S3 Gold Zone → Athena → QuickSight
為替API(モック) ─┘
```

---

## 前提条件

### 必要なツール

| ツール | バージョン | 用途 |
|--------|-----------|------|
| AWS CLI | v2以上 | AWSリソース操作 |
| Terraform | v1.5以上 | インフラプロビジョニング |
| Python | 3.10以上 | データ生成・アップロード |
| pip | 最新版 | Pythonパッケージ管理 |

### インストール確認

```bash
aws --version
terraform --version
python3 --version
```

### AWS CLIの設定

```bash
aws configure
# AWS Access Key ID: [入力]
# AWS Secret Access Key: [入力]
# Default region name: ap-northeast-1
# Default output format: json
```

---

## プロジェクト構成

```
sample_dwh/
├── terraform/
│   ├── main.tf                   # プロバイダ設定
│   ├── s3.tf                     # S3バケット定義
│   ├── glue.tf                   # Glueジョブ定義
│   ├── athena.tf                 # Athenaワークグループ定義
│   ├── variables.tf              # 変数定義
│   └── terraform.tfvars.example  # 環境固有値のサンプル（コピーして使用）
├── scripts/
│   ├── generate_data.py # モックデータ生成・S3アップロード
│   └── glue_job.py      # Glueジョブ本体（S3にアップロードして使用）
├── athena/
│   └── create_tables.sql
├── docs/
│   └── procedure.md
└── .gitignore           # terraform state・Pythonキャッシュ等を除外
```

---

## Step 1: Terraformでインフラ構築

### 1-1. ディレクトリ作成

```bash
mkdir -p terraform scripts athena
```

### 1-2. Terraformファイルの作成

#### `terraform/variables.tf`

```hcl
variable "project_name" {
  default = "sample-dwh"
}

variable "region" {
  default = "ap-northeast-1"
}

variable "aws_account_id" {
  description = "AWSアカウントID"
}
```

#### `terraform/main.tf`

```hcl
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.region
}
```

#### `terraform/s3.tf`

```hcl
# Raw Zone（収集したJSONをそのまま保存）
resource "aws_s3_bucket" "raw_zone" {
  bucket = "${var.project_name}-raw-zone"
}

# Gold Zone（加工済みParquetを保存）
resource "aws_s3_bucket" "gold_zone" {
  bucket = "${var.project_name}-gold-zone"
}

# GlueスクリプトとAthenaクエリ結果の保存先
resource "aws_s3_bucket" "scripts" {
  bucket = "${var.project_name}-scripts"
}
```

#### `terraform/glue.tf`

```hcl
resource "aws_iam_role" "glue_role" {
  name = "${var.project_name}-glue-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "glue.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "glue_s3" {
  role       = aws_iam_role.glue_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
}

resource "aws_iam_role_policy_attachment" "glue_service" {
  role       = aws_iam_role.glue_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole"
}

resource "aws_glue_job" "etl_job" {
  name         = "${var.project_name}-etl"
  role_arn     = aws_iam_role.glue_role.arn
  glue_version = "4.0"

  command {
    script_location = "s3://${aws_s3_bucket.scripts.bucket}/glue_job.py"
    python_version  = "3"
  }

  default_arguments = {
    "--RAW_BUCKET"  = aws_s3_bucket.raw_zone.bucket
    "--GOLD_BUCKET" = aws_s3_bucket.gold_zone.bucket
    "--TempDir"     = "s3://${aws_s3_bucket.scripts.bucket}/tmp/"
  }

  number_of_workers = 2
  worker_type       = "G.1X"
}
```

#### `terraform/athena.tf`

```hcl
resource "aws_athena_workgroup" "main" {
  name = "${var.project_name}-workgroup"

  # クエリ実行履歴が残っていても terraform destroy で削除できるようにする
  force_destroy = true

  configuration {
    result_configuration {
      output_location = "s3://${aws_s3_bucket.scripts.bucket}/athena-results/"
    }
  }
}

resource "aws_glue_catalog_database" "main" {
  name = replace(var.project_name, "-", "_")
}
```

#### `terraform/terraform.tfvars.example`

`aws_account_id` などの環境固有値はコマンドラインの `-var` ではなく `terraform.tfvars` で管理する。サンプルをコミットしておき、実値を入れた `terraform.tfvars` は `.gitignore` で除外する。

```hcl
# Copy this file to terraform.tfvars and fill in your actual values.
# terraform.tfvars is gitignored — never commit real account IDs.

aws_account_id = "123456789012"

# Optional overrides (defaults defined in variables.tf):
# project_name = "sample-dwh"
# region       = "ap-northeast-1"
```

#### `.gitignore`（プロジェクトルート）

```gitignore
# Terraform
**/.terraform/*
*.tfstate
*.tfstate.*
.terraform.lock.hcl
*.tfvars
!*.tfvars.example

# Python
__pycache__/
*.py[cod]
.venv/

# macOS
.DS_Store
```

### 1-3. Terraformの実行

```bash
cd terraform

# 環境固有値ファイルを用意（terraform.tfvars は .gitignore 対象）
cp terraform.tfvars.example terraform.tfvars
# terraform.tfvars を開き、aws_account_id を実際のアカウントIDに変更する

# 初期化
terraform init

# 実行計画の確認（terraform.tfvars が自動で読み込まれる）
terraform plan

# インフラ作成
terraform apply
```

---

## Step 2: Glueジョブスクリプトの作成・アップロード

### 2-1. `scripts/glue_job.py` の作成

このスクリプトが行うこと：
- S3 Raw ZoneのJSONを読み込む
- 購入IDの重複チェック（データ品質テスト）
- ドルを円に換算
- Parquet形式（Snappy圧縮）でGold Zoneに書き込む
- 日付・店舗でパーティション分割

```python
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
# 収集データは sales/YYYY/MM/DD/ のようにネストして保存されるため、
# recursiveFileLookup でサブディレクトリを再帰的に読み込む
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
```

### 2-2. スクリプトをS3にアップロード

```bash
# バケット名は terraform apply の出力から確認する
aws s3 cp scripts/glue_job.py s3://sample-dwh-scripts/glue_job.py
```

---

## Step 3: モックデータの生成・アップロード

### 3-1. Pythonパッケージのインストール

Homebrew等で導入したPythonはPEP 668により直接 `pip install` できない（`externally-managed-environment` エラー）。仮想環境を作成してインストールする。`generate_data.py` が使うのは `boto3` のみ。

```bash
# プロジェクトルートで仮想環境を作成・有効化
python3 -m venv .venv
source .venv/bin/activate

pip install boto3
```

### 3-2. `scripts/generate_data.py` の作成

```python
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
```

### 3-3. スクリプトの実行

```bash
# .venv を有効化した状態で実行する（3-1参照）
python3 scripts/generate_data.py
```

### 3-4. アップロード確認

```bash
aws s3 ls s3://sample-dwh-raw-zone/sales/ --recursive
aws s3 ls s3://sample-dwh-raw-zone/currency/ --recursive
```

---

## Step 4: Glueジョブの実行

### 4-1. GlueコンソールからETLを実行

```bash
aws glue start-job-run --job-name sample-dwh-etl
```

### 4-2. 実行状況の確認

```bash
# ジョブ実行IDを取得して状態を確認
aws glue get-job-runs --job-name sample-dwh-etl --query "JobRuns[0].{Status:JobRunState,Started:StartedOn}"
```

状態が `SUCCEEDED` になるまで待つ（2〜5分程度）。

### 4-3. Gold Zoneの出力確認

```bash
aws s3 ls s3://sample-dwh-gold-zone/sales/ --recursive
```

パーティション（例: `date=2026-05-14/store=Store A/`）が作成されていれば成功。

---

## Step 5: Athenaでテーブル定義・クエリ確認

### 5-1. `athena/create_tables.sql` の作成

```sql
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
```

### 5-2. Athenaコンソールでクエリ実行

AWSコンソール → Athena → クエリエディタ で以下を順番に実行する。

```sql
-- ① テーブル作成
-- athena/create_tables.sql の内容を貼り付けて実行

-- ② パーティションを認識させる
MSCK REPAIR TABLE sample_dwh.sales;

-- ③ 動作確認クエリ
SELECT store, date, SUM(sales_jpy) AS total_sales_jpy
FROM sample_dwh.sales
GROUP BY store, date
ORDER BY date DESC, total_sales_jpy DESC;
```

---

## Step 6: QuickSight（Amazon Quick）でダッシュボード作成

> QuickSight は現在 **Amazon Quick（Quick Suite）** に刷新されており、UI・メニュー名が旧版と異なる。以下は新UIでの手順。

### 6-1. Amazon Quick のセットアップ

1. AWSコンソール → QuickSight（Amazon Quick）→ サインアップ
2. サブスクリプションを選択（旧 Standard 相当。無料トライアルあり）

### 6-2. Athena・S3 へのアクセス権限を付与

データセット作成より先に、Amazon Quick から Athena と S3 を読めるよう権限を付与する。これを忘れるとデータセット作成時に S3 アクセスエラーになる。

1. 右上のアカウントメニュー → 「アカウントを管理」
2. 左サイドバー「アクセス許可」→ **「AWS リソース」**（ショートカットの「AWS リソース」カードでも可）
3. 「これらのリソースへのアクセスと自動検出を許可する」で:
   - **Amazon Athena** にチェック
   - **Amazon S3** にチェック →「S3 バケットを選択する」から以下2つを選択
     - `sample-dwh-gold-zone`（加工済みデータ本体）
     - `sample-dwh-scripts`（Athenaクエリ結果の出力先）
4. 「保存」

### 6-3. データセットの接続

1. 左サイドバー「データセット」→ 新しいデータセット → **Athena**
2. 「新規 Amazon Athena データソース」:
   - データソース名: 任意（例: `sample-dwh-workgroup`）
   - Athena ワークグループ: `sample-dwh-workgroup`
   - 「検証」して「検証済み」になることを確認 → 「データソースを作成」
3. 「テーブルの選択」:
   - カタログ: `AwsDataCatalog`
   - データベース: `sample_dwh`
   - テーブル: `sales`（「カスタム SQL を使用」は不要）
4. 「選択」→「直接クエリ」を選んで保存

### 6-4. ダッシュボードの作成

1. 作成したデータセットから分析を開始
2. 「新規シート」では **インタラクティブシート**（レイアウト・表示幅はデフォルトで可）を選んで「作成」
3. 「+ 追加」でビジュアルを追加し、以下2つを作成:

| ビジュアル種別 | X軸 | 値 | 色（グループ） |
|--------------|-----|-----|---------|
| 折れ線グラフ | date | sales_jpy（自動で合計） | store |
| 垂直棒グラフ | store | sales_jpy（自動で合計） | - |

4. 右上「公開」→「ダッシュボードとして公開」→ 名前を入力して保存

---

## 後片付け（リソース削除）

学習完了後、課金を止めるためにリソースを削除する。

```bash
# S3バケットの中身を空にする（バケット削除前に必要）
aws s3 rm s3://sample-dwh-raw-zone  --recursive
aws s3 rm s3://sample-dwh-gold-zone --recursive
aws s3 rm s3://sample-dwh-scripts   --recursive

# Terraformでインフラを削除
cd terraform
terraform destroy
```

> **注意**: QuickSight（Amazon Quick）のサブスクリプションは Terraform 管理外。課金停止には下記の手動解約が必要。

### Amazon Quick（QuickSight）の解約

S3・Glue・Athena は `terraform destroy` で削除されるが、Amazon Quick のサブスクリプションは別途コンソールから手動で解約する。

**前提条件**

- Amazon Quick を作成したときの IAM ユーザー / AWS ルートアカウントでサインインしていること
- Amazon Quick の **Admin ロール**を持っていること（`quicksight:Unsubscribe` 等の権限）
- 解約しても AWS アカウント自体は削除されない（Amazon Quick のみ削除）

**手順**

1. プロフィールアイコン → **「Manage Quick（Quick の管理）」** を選択
2. **「アカウント設定」→「管理（Manage）」** をクリック（→「アカウント終了」画面が開く）
   - UIにアクセスできない場合は直接リンク: `https://ap-northeast-1.quicksight.aws.amazon.com/sn/console/unsubscribe`
3. 「アカウント終了」画面でアカウント名が正しいことを確認
4. **「アカウント終了保護」をオフ**に切り替える（→「アカウントを削除」セクションが有効になる）
5. 確認欄に画面表示の確認ワード（`confirm`）を入力して実行

> **警告**: 削除は即時かつ恒久的で復元不可。**全リージョン**のダッシュボード・分析・データセット・データソース・ユーザーがすべて削除される。本番環境では事前にエクスポート・バックアップを行うこと。
>
> 出典: [Account details in Amazon Quick](https://docs.aws.amazon.com/quicksuite/latest/userguide/manage-qs-account-settings.html) / [Deleting your Amazon QuickSight subscription](https://docs.aws.amazon.com/quicksight/latest/user/closing-account.html)

---

## トラブルシューティング

| 現象 | 確認事項 |
|------|---------|
| Glueジョブが `FAILED` | CloudWatch Logs (`/aws-glue/jobs/error`) でエラーログを確認 |
| Athenaで「テーブルが見つからない」 | `MSCK REPAIR TABLE` を再実行 |
| S3アップロードで権限エラー | `aws configure` で正しいクレデンシャルが設定されているか確認 |
| Glueジョブで品質エラー | Raw ZoneのJSONに重複 `purchase_id` がないか確認 |
| `terraform destroy` で `WorkGroup is not empty` | クエリ実行履歴が残っているため。`athena.tf` の `force_destroy = true` で解消。既存環境は `aws athena delete-work-group --work-group sample-dwh-workgroup --recursive-delete-option` で手動削除 |

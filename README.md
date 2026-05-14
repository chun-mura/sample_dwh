# sample_dwh — 売上データ可視化のためのデータ分析基盤

書籍『エンジニアのためのデータ分析基盤入門』第9章「[事例で考える]データ分析基盤のアーキテクチャ設計」をもとに構築した、学習用のデータ分析基盤です。データの収集から可視化までを AWS 上で一気通貫に体験することを目的としています。

## アーキテクチャ

AWS を使った4レイヤー構成のデータ分析基盤です。

```
売上API(モック) ─┐
                ├─→ S3 Raw Zone → Glue(加工) → S3 Gold Zone → Athena → QuickSight
為替API(モック) ─┘
```

| レイヤー | 役割 | 使用サービス |
|---------|------|------------|
| コレクティング（収集） | API から取得した JSON をそのまま保存 | S3 Raw Zone |
| プロセシング（処理） | ドル→円換算、品質テスト、Parquet 変換 | AWS Glue (Spark) |
| ストレージ（保存） | 加工済みデータを日付・店舗でパーティション保存 | S3 Gold Zone |
| アクセス（提供） | SQL での参照とダッシュボード化 | Athena / QuickSight (Amazon Quick) |

アーキテクチャ図: [`docs/architecture.png`](docs/architecture.png)

## プロジェクト構成

```
sample_dwh/
├── terraform/        # インフラ定義（S3 / Glue / Athena / IAM）
├── scripts/
│   ├── generate_data.py  # モックデータ生成・S3アップロード
│   └── glue_job.py       # Glue ETL ジョブ本体
├── athena/
│   └── create_tables.sql # Athena 外部テーブル定義
└── docs/
    ├── procedure.md      # 構築手順書（詳細）
    ├── plan.md           # 学習プランの元案
    └── architecture.png  # アーキテクチャ図
```

## 前提ツール

| ツール | バージョン |
|--------|-----------|
| AWS CLI | v2 以上 |
| Terraform | v1.5 以上 |
| Python | 3.10 以上 |

AWS CLI に `ap-northeast-1` リージョンのクレデンシャルが設定されている必要があります。

## 使い方

構築から後片付けまでの詳細な手順は [`docs/procedure.md`](docs/procedure.md) を参照してください。大まかな流れは以下の通りです。

1. **Step 1**: Terraform で S3 / Glue / Athena / IAM を構築
2. **Step 2**: Glue ジョブスクリプトを S3 にアップロード
3. **Step 3**: モックデータ（売上・為替）を生成して Raw Zone にアップロード
4. **Step 4**: Glue ETL ジョブを実行し、Gold Zone に Parquet を出力
5. **Step 5**: Athena でテーブル定義・クエリ確認
6. **Step 6**: QuickSight (Amazon Quick) でダッシュボードを作成

## 後片付け

学習完了後は課金を止めるためにリソースを削除します（詳細は [`docs/procedure.md`](docs/procedure.md) の「後片付け」セクション）。

- S3 バケットを空にして `terraform destroy`
- QuickSight (Amazon Quick) のサブスクリプションは Terraform 管理外のため、コンソールから手動で解約

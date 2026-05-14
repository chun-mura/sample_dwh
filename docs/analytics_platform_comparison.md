# Analytics Platform Comparison

データ規模・同時接続ユーザー数・コストごとの最適なアーキテクチャ選択指針。

対象サービス: Amazon Athena / Amazon Redshift / Google BigQuery / Databricks / Snowflake / ClickHouse / Azure Synapse (Microsoft Fabric) / Firebolt / StarRocks / Palantir Foundry

---

## データ規模 × ユースケース別の推奨

| データ規模 | 主用途 | 推奨プラットフォーム |
|-----------|--------|---------------------|
| < 1TB | アドホック探索・ログ分析 | **Athena**（固定コストゼロ）/ **DuckDB**（ローカル分析） |
| 1〜10TB | 定常BI・ダッシュボード | **Redshift Serverless** / **Snowflake** / **BigQuery** |
| 10〜100TB | BI + ETL 混在・中規模DWH | **Snowflake**（BI強）/ **Databricks**（ETL・ML強）/ **BigQuery**（GCP環境） |
| 10〜100TB | リアルタイム・高並列分析 | **ClickHouse** / **StarRocks** / **Firebolt** |
| 100TB〜PB | 大規模DWH・ML・ストリーミング | **Databricks**（ETL/ML）/ **Snowflake**（BI/DWH）/ **BigQuery** |
| PB超・複雑オペレーション | ミッションクリティカル・現場AI | **Palantir Foundry** |

---

## 同時接続ユーザー数別の推奨

| 同時接続数 | 推奨 |
|-----------|------|
| 〜20人 | **Athena**（デフォルト上限 20クエリ） |
| 20〜100人 | **Redshift** / **Snowflake Standard** / **BigQuery** |
| 100〜1,000人 | **Snowflake Enterprise**（Multi-Cluster）/ **Databricks** / **BigQuery** |
| 1,000人超（外部公開含む） | **ClickHouse** / **Firebolt** / **StarRocks**（高並列・低レイテンシ） |
| 1,000人超（社内BI） | **Snowflake Enterprise** / **Databricks Serverless SQL** |

---

## 月次コスト目安

※以下の金額は 2024〜2025 年の一般的な導入事例をベースにした目安レンジであり、ワークロード・リージョン・割引条件により大きく変動します。

| | 小規模チーム | 中規模 | 大規模エンタープライズ |
|---|---|---|---|
| **Athena** | $0〜数百ドル | $1,000〜$10,000 | 最適化必須・青天井リスク |
| **Redshift** | $500〜$1,500 | $2,000〜$20,000 | 予約割引で大幅減 |
| **BigQuery** | $0〜数百ドル | $1,000〜$5,000 | $5,000〜$50,000+ |
| **Databricks** | $1,500〜$3,000 | $10,000〜$30,000 | $70,000〜$90,000+ |
| **Snowflake** | $1,000〜$3,000 | $10,000〜$40,000 | $50,000〜$100,000+ |
| **ClickHouse Cloud** | $1〜$500 | $500〜$5,000 | $100,000+ |
| **Azure Synapse / Fabric** | $260〜$600 | $1,000〜$10,000 | 予約割引で最大65%減 |
| **Firebolt** | $200〜 | $500〜要商談 | 要商談 |
| **StarRocks** | 無料（OSS） | 無料〜商用要商談 | 商用要商談 |
| **Palantir** | 非対応 | 非対応 | 年間$1M+〜（交渉制・定価非公開） |

---

## 各サービス詳細

### Amazon Athena

**料金**: スキャン課金 $5/TB（最低 10MB 課金）、Provisioned Capacity おおよそ $0.30〜$0.40/DPU 時間（リージョン・時期により変動）

**強み**
- サーバーレスでインフラ管理不要
- S3 上のデータをそのままクエリ可能（ETL 不要）
- AWS Glue カタログとのシームレスな統合
- スモールスタート向き（固定コストゼロ）

**弱み**
- 同時実行クエリ上限が低い（デフォルト 20 クエリ）
- スキャン料金の罠（CSV/JSON のまま使うと高額）
- 一貫した SLA が保証しにくい

**コスト最適化のポイント**: Parquet + パーティション化で劇的に削減可能
（例: 最適化なし $30,000/月 → 最適化後 $1.50/月）

**典型的なユースケース**: アドホック分析、ログ調査、S3 データレイクへのスポットクエリ

---

### Amazon Redshift

**料金**
- Provisioned: $0.543/ノード時間〜（ra3.xlplus）、1〜3 年予約で最大 75% 割引
- Serverless: ~$0.375/RPU 時間（最低 4 RPU）
- ストレージ: Managed Storage $0.024/GB/月

**強み**
- 大規模 BI・レポート用途で実績あり
- Concurrency Scaling で同時接続を自動拡張（1 日 1 時間無料）
- Provisioned で予測可能なコスト
- AWS エコシステムとの深い統合

**弱み**
- AWS 専用（マルチクラウド不可）
- Provisioned はコンピュートとストレージが結合
- ML・データサイエンス用途は限定的

**典型的なユースケース**: 企業内 BI レポート、定期バッチ分析、中〜大規模の定常ワークロード

---

### Google BigQuery

**料金**
- オンデマンド: $6.25/TB スキャン（毎月 1TB 分のクエリ無料枠 + 10GB ストレージ無料枠あり）
- Standard Edition: $0.04/スロット時間
- Enterprise Edition: $0.06/スロット時間（1年契約 $0.048、3年 $0.036）
- ストレージ: $0.02/GiB/月（90 日未変更で $0.01 に自動減額）

**強み**
- サーバーレス・完全マネージド（インフラ管理不要）
- GCP エコシステムとの深い統合（Vertex AI、Looker、Dataflow、Pub/Sub）
- BigQuery ML によるモデルトレーニング・推論を SQL で直書き可能
- BigQuery Omni で AWS/Azure データのクロスクラウドクエリ
- 同時接続数が事実上無制限（スロット数に依存）

**弱み**
- コスト予測困難（オンデマンドは大規模スキャン時に費用が跳ね上がる）
- トランザクション処理（OLTP）には不向き
- GCP 外での利用は Omni 経由で制約あり
- 小規模クエリが多い場合は割高

**典型的なユースケース**: GCP 上のデータウェアハウス、マーケティング分析、ML パイプライン、BI レポーティング

---

### Databricks

**料金**: DBU（Databricks Unit）ベース課金 + クラウドプロバイダー費用（VM・ストレージ）が別途

**強み**
- Apache Spark ベースの大規模データ処理・ML 統合
- Delta Lake によるオープンフォーマット（ベンダーロックインが少ない）
- データエンジニアリング・DS・ML・SQL が一プラットフォームで完結
- AWS/Azure/GCP マルチクラウド対応
- 大規模 ETL・PB スケール処理では Snowflake より 20〜40% 安い傾向

**弱み**
- 技術者向け（データエンジニア・DS が主）、ビジネスユーザーには難しい
- コスト予測が複雑（DBU + クラウドコストの二重構造）
- BI クエリ速度は Snowflake に 15〜30% 劣る傾向

**典型的なユースケース**: 大規模 ETL パイプライン、機械学習モデル開発・運用、ストリーミング処理

---

### Snowflake

**料金**
- コンピュート: $2〜4/クレジット（エディション・リージョンにより変動）
- ストレージ: オンデマンド $40/TB/月、事前購入 $23/TB/月
- データは圧縮で通常 50〜70% 削減

**強み**
- コンピュートとストレージの完全分離（独立スケーリング）
- マルチクラウド対応（AWS/Azure/GCP）
- SQL フレンドリーで分析エンジニア・BI アナリストに使いやすい
- Data Sharing エコシステムが充実
- 運用管理がほぼ不要（フルマネージド）

**弱み**
- 大規模 ETL・ML は Databricks と比較してコスト高になりやすい
- ウェアハウスのコールドスタートレイテンシ（最低 60 秒課金）
- 利用が増えると予想外に高額になりやすい

**典型的なユースケース**: エンタープライズ DWH、BI ダッシュボード、セルフサービスアナリティクス、データマーケットプレイス

---

### ClickHouse Cloud

**料金**
- コンピュート: ~$0.22/時（開発）〜 $0.75/コンピュートユニット時（本番）
- ストレージ: ~$25.30/TiB/月
- データ転出料: $115.20/TiB（2025年1月より新設）
- セルフホスト版はオープンソース（Apache 2.0）

**強み**
- 超高速 OLAP クエリ（ms〜sub-second）
- 高圧縮率（競合比 4〜10 倍のコスト効率を主張）
- 高並列性能：水平スケールで同時実行数とシングルクエリ速度を両立
- 70+ ファイルフォーマット対応、Iceberg/Hive カタログ統合
- 外部公開ダッシュボード（SaaS プロダクト組み込み）に特に強い

**弱み**
- 複雑な JOIN（スタースキーマ等）では専用 DWH に劣る場合がある
- 2025年1月の価格改定でコスト優位が縮小・エグレス料金でロックイン懸念
- Snowflake/BigQuery ほどの BI ツール連携エコシステムが発展途上

**典型的なユースケース**: リアルタイム分析、埋め込みアナリティクス（SaaS 内）、ログ/イベント分析、高頻度広告オークション分析

---

### Azure Synapse Analytics / Microsoft Fabric

> Microsoft は 2023〜2024 年に Synapse の後継として **Microsoft Fabric** を GA。新規プロジェクトは Fabric 推奨。

**料金**
- Synapse Dedicated SQL Pool: DW100c ~$1,102/月〜、1〜3 年予約で最大 65% 割引
- Microsoft Fabric: F2（最小）~$263/月、F64 ~$8,400/月

**強み**
- Azure エコシステムとの完全統合（Power BI、ADF、Purview、ADLS）
- Fabric: Power BI との深い統合、SaaS モデルで運用コスト低減
- オンプレ SQL Server からの移行コストが最小
- Synapse: SQL + Spark + Data Explorer を単一ワークスペースで統合

**弱み**
- 複雑な学習曲線（多コンポーネント構成）
- Synapse の DWU スケール変更中は数分間サービス停止
- Fabric は重い Spark ジョブが BI レポートに影響することがある（CU 共有）

**典型的なユースケース**: Azure 上のエンタープライズ DWH、Microsoft 365/Power BI ユーザー向けレポーティング、SQL Server からのクラウド移行先

---

### Firebolt

**料金**
- コンピュート: $0.35/FBU 時（S ノード: 8 FBU、M ノード: 16 FBU）
- ストレージ: $23/TiB/月（AWS S3 直接）
- 秒単位課金、アイドル時はほぼ無課金

**強み**
- 超低レイテンシ・高スループット（Similarweb が 1PB 超で sub-second クエリを実現）
- エンジン粒度でのコンピュート分離（BI/ETL/アドホックを別エンジンに分割可）
- カスタマー向け（外部公開）アナリティクスに強い

**弱み**
- エコシステムが小さい（コミュニティ・サードパーティ連携が限定的）
- 主に AWS（Azure 対応は限定的）
- 大規模は要商談で価格が非透明

**典型的なユースケース**: SaaS プロダクト内の顧客向け分析ダッシュボード、広告テック、1ms〜数十ms の API 応答が求められるアプリケーション

---

### StarRocks

**料金**: オープンソース（Apache 2.0）はセルフホスト無料。クラウド版（CelerData）は商用要商談

**強み**
- MPP アーキテクチャで結合・集計クエリが高速
- リアルタイム OLAP: CDC / ストリーミングデータの即時クエリ対応
- Apache Iceberg / Delta Lake / Hudi とのレイクハウス統合
- マテリアライズドビューが強力（インクリメンタル更新対応）
- WeChat、Trip.com など PB 級実績あり

**弱み**
- クラウドマネージド版の成熟度は ClickHouse Cloud / BigQuery より低い
- 商用サポートなしのセルフホストは運用コストが高い

**典型的なユースケース**: リアルタイムアナリティクス、BI ダッシュボード、ユーザー行動分析、ゲーム・EC・金融の大規模集計

---

### Palantir Foundry / AIP

**料金**: 公式な定価は非公開。大規模エンタープライズ向けに年間数百万ドル規模（$1M+/年）の交渉ベース契約が一般的とされる。コンピュート秒・ストレージ・オントロジーの 3 軸課金

**強み**
- 複雑・多様なデータソースを統合するセマンティックオントロジー層
- ノーコード/ローコード UI で非技術ユーザーが AI を活用可能
- AIP によるオペレーショナル AI（現場意思決定の自動化）
- 政府・防衛・製造・医療などミッションクリティカル用途での実績
- データガバナンスと監査追跡が組み込み

**弱み**
- 圧倒的に高い参入障壁（最低 $10M/年〜）
- 高度なオンボーディング・専門トレーニングが必要（6〜12 ヶ月）
- 汎用アナリティクス基盤としてはオーバースペック
- ベンダーロックインが強い

**典型的なユースケース**: 政府・防衛機関のオペレーション、大企業のサプライチェーン最適化、複数システムのデータ統合と現場 AI エージェント

---

## その他プラットフォームの評価サマリ

| プラットフォーム | 推奨度 | 理由 |
|---|---|---|
| **DuckDB** | 限定的（小〜中規模） | 組み込み単一プロセス。〜1億行規模のローカル/ノートブック分析に最適。マルチユーザー本番 DWH には不向き |
| **Starburst (Trino)** | 中程度 | データレイク上の SQL フェデレーションに強い。既存データを移動せずクエリしたい場合に有効。単体 DWH としては弱め |
| **Apache Doris** | 中程度 | StarRocks のフォーク元。中国企業での採用実績は多いがグローバル商用エコシステムは StarRocks に遅れ |
| **Oracle Autonomous DWH** | 中程度（Oracle 既存ユーザー向け） | Oracle Exadata 上で自律運用。Oracle DB 資産が多い組織向け。ベンダーロックイン強し |
| **IBM Netezza** | 低い（レガシー） | クラウド版も存在するが新規採用は少ない。レガシー移行先として検討程度 |

---

## 段階的移行パターン（このプロジェクト向け）

```
[現在] Athena + Glue + S3
    ↓ 同時接続 20人超 or スキャンコスト増大
[Step 1] Redshift Serverless（AWS エコシステム維持）
         または BigQuery（GCP 移行を検討する場合）
    ↓ データ 10TB超 or マルチクラウド・ML 需要
[Step 2] Snowflake（BI 重視）または Databricks（ETL/ML 重視）
         リアルタイム・高並列が必要なら ClickHouse / StarRocks
    ↓ ミッションクリティカル・現場 AI 自動化
[Step 3] Palantir Foundry（大企業・政府専用）
```

移行判断の目安:
- 月次 Athena スキャンコストが **$500 超**
- BI ダッシュボードの同時利用が **10人超**
- クエリ応答が **数十秒かかる**ようになった

---

## 参考情報源

- [Amazon Athena Pricing](https://aws.amazon.com/athena/pricing/)
- [Amazon Redshift Pricing](https://aws.amazon.com/redshift/pricing/)
- [Amazon Redshift Concurrency Scaling](https://aws.amazon.com/redshift/features/concurrency-scaling/)
- [BigQuery Pricing | Google Cloud](https://cloud.google.com/bigquery/pricing)
- [BigQuery Editions | Google Cloud Blog](https://cloud.google.com/blog/products/data-analytics/introducing-new-bigquery-pricing-editions)
- [Databricks Pricing](https://www.databricks.com/product/pricing)
- [Snowflake Pricing Explained | select.dev](https://select.dev/posts/snowflake-pricing)
- [ClickHouse Pricing Change Jan 2025 | Quesma Blog](https://quesma.com/blog/clickhouse-pricing/)
- [ClickHouse vs Snowflake for Real-Time Analytics](https://clickhouse.com/blog/clickhouse-vs-snowflake-for-real-time-analytics-comparison-migration-guide)
- [Azure Synapse Analytics Pricing | Microsoft Azure](https://azure.microsoft.com/en-us/pricing/details/synapse-analytics/)
- [Azure Synapse vs Microsoft Fabric | chaosgenius.io](https://www.chaosgenius.io/blog/azure-synapse-vs-fabric/)
- [Firebolt Pricing](https://www.firebolt.io/pricing)
- [StarRocks 2025 Year in Review](https://www.starrocks.io/blog/starrocks-2025-year-in-review)
- [Palantir Foundry Plans](https://www.palantir.com/platforms/foundry/plans/)
- [Databricks vs Snowflake vs Redshift | ISHIR](https://www.ishir.com/blog/122362/databricks-vs-snowflake-vs-redshift-a-2024-face-off.htm)
- [Palantir vs Snowflake vs Databricks | i4C](https://www.i4c.com/palantir-vs-snowflake-vs-databricks-which-one-fits-your-business/)
- [Top Real-Time OLAP Databases 2025 | RisingWave](https://risingwave.com/blog/top-real-time-olap-databases-in-2025/)
- [Fivetran Cloud Data Warehouse Benchmark](https://www.fivetran.com/blog/warehouse-benchmark)

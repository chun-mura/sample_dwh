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

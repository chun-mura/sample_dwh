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

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

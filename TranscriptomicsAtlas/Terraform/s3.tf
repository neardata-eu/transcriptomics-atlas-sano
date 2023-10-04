data "aws_s3_bucket" "NearData_results_bucket_name" {
  bucket = "neardata-salmon-ec2-results"
}

data "aws_s3_bucket" "NearData_results_bucket_name_low_mr" {
  bucket = "neardata-salmon-ec2-results-low-mr"
}

data "aws_s3_bucket" "NearData_container_results_bucket_name" {
  bucket = "neardata-salmon-hpc-results"
}

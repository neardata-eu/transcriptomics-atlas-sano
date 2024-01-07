data "aws_s3_bucket" "NearData_results_bucket_name" {
  bucket = "transcriptomics-atlas"
}

data "aws_s3_bucket" "NearData_results_hpc_bucket_name" {
  bucket = "neardata-salmon-hpc-results"
}


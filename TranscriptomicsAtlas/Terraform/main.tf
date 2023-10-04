provider "aws" {
  default_tags {
    tags = {
      Project = "NearData"
    }
  }
}

data "aws_iam_instance_profile" "NearData_ec2_role" {
  name = "neardata-ec2-role"
}

resource "aws_ssm_parameter" "ec2_cwagent_config" {
  name        = "ec2_cwagent_config"
  description = "Cloudwatch agent config for Transcriptomics Atlas EC2 instances"
  type        = "String"
  value       = file("${path.module}/../EC2/ec2_cwagent_config.json")
  tier        = "Advanced"
}


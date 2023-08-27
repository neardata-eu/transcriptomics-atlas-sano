data "aws_s3_bucket" "NearData_results_bucket_name" {
  bucket = "neardata-salmon-ec2-results"
}

data "aws_s3_bucket" "NearData_metadata_bucket_name" {
  bucket = "neardata-salmon-ec2-metadata"
}

data "aws_s3_bucket" "NearData_container_results_bucket_name" {
  bucket = "neardata-salmon-hpc-results"
}

data "aws_s3_bucket" "NearData_container_metadata_bucket_name" {
  bucket = "neardata-salmon-hpc-metadata"
}

data "aws_iam_instance_profile" "NearData_ec2_role" {
  name = "neardata-ec2-role"
}

resource "aws_sqs_queue" "NearData_queue" {
  name                       = "NearData_queue"
  max_message_size           = 2048
  message_retention_seconds  = 36000
  receive_wait_time_seconds  = 5
  visibility_timeout_seconds = 18000

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.NearData_deadletter_queue.arn
    maxReceiveCount     = 1
  })

  tags = {
    Project = "NearData"
  }
}

resource "aws_sqs_queue" "NearData_deadletter_queue" {
  name                       = "NearData_deadletter_queue"
  max_message_size           = 2048
  message_retention_seconds  = 604800
  receive_wait_time_seconds  = 5
  visibility_timeout_seconds = 10800

  tags = {
    Project = "NearData"
  }
}

resource "aws_sqs_queue" "NearData_queue_container" {
  name                       = "NearData_queue_container"
  max_message_size           = 2048
  message_retention_seconds  = 36000
  receive_wait_time_seconds  = 5
  visibility_timeout_seconds = 18000

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.NearData_deadletter_queue_container.arn
    maxReceiveCount     = 1
  })

  tags = {
    Project = "NearData"
  }
}

resource "aws_sqs_queue" "NearData_deadletter_queue_container" {
  name                       = "NearData_deadletter_queue_container"
  max_message_size           = 2048
  message_retention_seconds  = 604800
  receive_wait_time_seconds  = 5
  visibility_timeout_seconds = 10800

  tags = {
    Project = "NearData"
  }
}

resource "aws_ssm_parameter" "queue_name" {
  name  = "/neardata/queue_name"
  type  = "String"
  value = aws_sqs_queue.NearData_queue.name

  tags = {
    Project = "NearData"
  }
}

resource "aws_ssm_parameter" "queue_name_container" {
  name  = "/neardata/queue_name_container"
  type  = "String"
  value = aws_sqs_queue.NearData_queue_container.name

  tags = {
    Project = "NearData"
  }
}

resource "aws_ssm_parameter" "s3_bucket" {
  name  = "/neardata/s3_bucket_name"
  type  = "String"
  value = data.aws_s3_bucket.NearData_results_bucket_name.bucket

  tags = {
    Project = "NearData"
  }
}

resource "aws_ssm_parameter" "s3_bucket_metadata" {
  name  = "/neardata/s3_bucket_metadata_name"
  type  = "String"
  value = data.aws_s3_bucket.NearData_metadata_bucket_name.bucket

  tags = {
    Project = "NearData"
  }
}

resource "aws_ssm_parameter" "s3_bucket_container" {
  name  = "/neardata/s3_bucket_name/container"
  type  = "String"
  value = data.aws_s3_bucket.NearData_container_results_bucket_name.bucket

  tags = {
    Project = "NearData"
  }
}

resource "aws_ssm_parameter" "s3_bucket_metadata_container" {
  name  = "/neardata/s3_bucket_metadata_name/container"
  type  = "String"
  value = data.aws_s3_bucket.NearData_container_metadata_bucket_name.bucket

  tags = {
    Project = "NearData"
  }
}

resource "aws_ssm_parameter" "ec2_cwagent_config" {
  name        = "ec2_cwagent_config"
  description = "Cloudwatch agent config for Transcriptomics Atlas EC2 instances"
  type        = "String"
  value       = file("${path.module}/../EC2/ec2_cwagent_config.json")
  tier        = "Advanced"
}

resource "aws_security_group" "NearData_sg" {
  name   = "NearData_SG"
  vpc_id = aws_vpc.NearData_VPC.id

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["195.150.12.215/32", "5.173.49.232/32", "94.254.191.79/32"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name    = "NearData_SG"
    Project = "NearData"
  }
}

resource "aws_launch_template" "NearData_lt" {
  name          = "NearData_lt"
  image_id      = "ami-0bf898f183b27114f"
  instance_type = "m6a.large"
  key_name      = "neardata-pk"
  user_data     = base64encode(file("init.sh"))
  ebs_optimized = true

  network_interfaces {
    security_groups             = [aws_security_group.NearData_sg.id]
    associate_public_ip_address = true
  }

  monitoring {
    enabled = true
  }

  iam_instance_profile {
    arn = data.aws_iam_instance_profile.NearData_ec2_role.arn
  }

  tags = {
    Project = "NearData"
  }

  tag_specifications {
    resource_type = "instance"

    tags = {
      Name    = "NearData_v2.1-lt"
      Project = "NearData"
    }
  }
}

#resource "aws_autoscaling_group" "NearData_asg" {
#  name                      = "NearData_asg"
#  min_size                  = 1
#  desired_capacity          = 8
#  max_size                  = 8
#  vpc_zone_identifier       = values(aws_subnet.NearData_Subnets)[*].id
#  wait_for_capacity_timeout = 0
#
#  launch_template {
#    id      = aws_launch_template.NearData_lt.id
#    version = "$Latest"
#  }
#}

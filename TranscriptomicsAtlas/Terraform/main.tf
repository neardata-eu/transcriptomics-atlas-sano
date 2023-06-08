data "aws_s3_bucket" "NearData_results_bucket_name" {
  bucket = "neardata-bucket-1234"
}

data "aws_s3_bucket" "NearData_metadata_bucket_name" {
  bucket = "neardata-bucket-1234-metadata"
}

data "aws_iam_instance_profile" "labRole_profile" {
  name = "LabInstanceProfile"
}

resource "aws_sqs_queue" "NearData_queue" {
  name                       = "NearData_queue"
  max_message_size           = 2048
  message_retention_seconds  = 10800
  receive_wait_time_seconds  = 5
  visibility_timeout_seconds = 10800

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

resource "aws_ssm_parameter" "queue_name" {
  name  = "/neardata/queue_name"
  type  = "String"
  value = aws_sqs_queue.NearData_queue.name

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

resource "aws_security_group" "NearData_sg" {
  name   = "NearData_SG"
  vpc_id = aws_vpc.NearData_VPC.id

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["195.150.12.215/32"]
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
  image_id      = "ami-0bbfdbe3656d3a4bb"
  instance_type = "m6a.large"
  key_name      = "vockey"
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
    arn = data.aws_iam_instance_profile.labRole_profile.arn
  }

  tags = {
    Project = "NearData"
  }

  tag_specifications {
    resource_type = "instance"

    tags = {
      Name    = "NearData_v12-lt"
      Project = "NearData"
    }
  }
}

resource "aws_autoscaling_group" "NearData_asg" {
  name                      = "NearData_asg"
  min_size                  = 1
  desired_capacity          = 4
  max_size                  = 5
  vpc_zone_identifier       = values(aws_subnet.NearData_Subnets)[*].id
  wait_for_capacity_timeout = 0

  launch_template {
    id      = aws_launch_template.NearData_lt.id
    version = "$Latest"
  }
}

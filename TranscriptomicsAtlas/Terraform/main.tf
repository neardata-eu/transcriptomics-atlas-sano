resource "aws_sqs_queue" "neardata_queue" {
  name                       = "neardata_queue"
  max_message_size           = 2048
  message_retention_seconds  = 3600
  receive_wait_time_seconds  = 5
  visibility_timeout_seconds = 2700  # TODO fine-tune

  tags = {
    Project = "NearData"
  }
}

#resource "aws_s3_bucket" "neardata_bucket" {
#  bucket_prefix = "neardata-bucket-"
#
#  tags = {
#    Project = "NearData"
#  }
#}

resource "aws_ssm_parameter" "queue_name" {
  name  = "/neardata/queue_name"
  type  = "String"
  value = aws_sqs_queue.neardata_queue.name
  tags  = {
    Project = "NearData"
  }
}

resource "aws_ssm_parameter" "s3_bucket" {
  name  = "/neardata/s3_bucket_name"
  type  = "String"
  value = "neardata-bucket-123"  # aws_s3_bucket.neardata_bucket.name
  tags  = {
    Project = "NearData"
  }
}


resource "aws_security_group" "neardata_sg" {
  name   = "neardata_sg"
  vpc_id = aws_vpc.neardata_vpc.id

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["5.173.33.80/32", "195.150.12.215/32", "5.173.48.40/32"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_iam_instance_profile" "labRole_profile" {
  name = "labRole_profile"
  role = "LabRole"  # FIXME later
}

resource "aws_launch_template" "neardata_lt" {
  name          = "neardata_lt"
  image_id      = "ami-0e8c160beeea8398b"
  instance_type = "m6a.large"
  key_name      = "vockey"

  user_data = base64encode(file("init.sh"))

  block_device_mappings {
    device_name = "/dev/sda1"  # ROOT

    ebs {
      volume_size = 150
      volume_type = "gp3"
      delete_on_termination = "true"
    }
  }

  network_interfaces {
    security_groups             = [aws_security_group.neardata_sg.id]
    associate_public_ip_address = true
  }

  iam_instance_profile {
    arn = aws_iam_instance_profile.labRole_profile.arn
  }
}

resource "aws_autoscaling_group" "neardata_asg" {
  name                = "neardata_asg"
  max_size            = 3
  min_size            = 1
  desired_capacity    = 1
  vpc_zone_identifier = [aws_subnet.subnet_1.id, aws_subnet.subnet_2.id, aws_subnet.subnet_3.id, aws_subnet.subnet_4.id]

  launch_template {
    id      = aws_launch_template.neardata_lt.id
    version = "$Latest"
  }
}



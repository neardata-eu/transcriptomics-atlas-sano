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
    Name = "NearData_SG"
  }
}

resource "aws_launch_template" "NearData_lt" {
  name          = "NearData_lt"
  image_id      = "ami-03c6be1fd52a83cda"
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

  instance_market_options {
    market_type = "spot"
    spot_options {
      instance_interruption_behavior = "terminate"  # TODO handle termination request in code
    }
  }

  block_device_mappings {
    device_name = "/dev/sda1"
    ebs {
      volume_size = 250
      volume_type = "gp3"
      iops        = 3000
      throughput  = 250
    }
  }

  tag_specifications {
    resource_type = "instance"

    tags = {
      Name = "NearData_v2.2-lt"
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
#
#  tag {
#    key                 = "Project"
#    value               = "NearData"
#    propagate_at_launch = true
#  }
#}

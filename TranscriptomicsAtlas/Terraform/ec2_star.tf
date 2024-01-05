resource "aws_launch_template" "STAR_lt" {
  name          = "STAR_lt"
  image_id      = "ami-088dcc39a7540d42b"
  instance_type = "r6a.4xlarge"
  key_name      = "neardata-pk2"
  user_data     = base64encode(file("init_STAR.sh"))
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

#  instance_market_options {
#    market_type = "spot"
#    spot_options {
#      instance_interruption_behavior = "terminate"
#    }
#  }

  block_device_mappings {
    device_name = "/dev/sda1"
    ebs {
      volume_size = 450
      volume_type = "gp3"
      iops        = 3000
      throughput  = 300
    }
  }

  tag_specifications {
    resource_type = "instance"

    tags = {
      Name = "STAR-v0.1"
    }
  }
}

#resource "aws_autoscaling_group" "STAR_asg" {
#  name                      = "STAR_asg"
#  min_size                  = 1
#  desired_capacity          = 1
#  max_size                  = 1
#  vpc_zone_identifier       = ["subnet-0a0b5127b11b04c16"] #values(aws_subnet.NearData_Subnets)[*].id
#  wait_for_capacity_timeout = 0
#
#  launch_template {
#    id      = aws_launch_template.STAR_lt.id
#    version = "$Latest"
#  }
#
#  tag {
#    key                 = "Project"
#    value               = "NearData"
#    propagate_at_launch = true
#  }
#}

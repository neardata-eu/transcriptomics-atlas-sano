resource "aws_launch_template" "NearData_lt" {
  name          = "NearData_lt"
  image_id      = "ami-03c6be1fd52a83cda"
  instance_type = "m6a.large"
  key_name      = "neardata-pk"
  user_data     = base64encode(file("init_Salmon.sh"))
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
      volume_size = 300
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

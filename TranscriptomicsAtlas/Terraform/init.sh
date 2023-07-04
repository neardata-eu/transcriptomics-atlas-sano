#!/usr/bin/env bash
/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -a fetch-config -m ec2 -c ssm:ec2_cwagent_config -s
su ubuntu -c "python3 /home/ubuntu/Consumer/consumer.py"
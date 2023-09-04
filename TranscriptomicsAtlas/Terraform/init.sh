#!/usr/bin/env bash
#/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -a fetch-config -m ec2 -c ssm:ec2_cwagent_config -s
#aws s3 sync s3://neardata-bucket-1234/source/ /opt/TAtlas
su ubuntu -c "python3 /opt/TAtlas/Consumer/consumer.py"
#!/usr/bin/env bash
/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -a fetch-config -m ec2 -c ssm:ec2_cwagent_config -s
aws s3 sync s3://neardata-src/source/Salmon /opt/TAtlas

{
echo export queue_name="NearData_queue"
echo export s3_bucket_name="neardata-salmon-ec2-results"
echo export s3_bucket_name_low_mr="neardata-salmon-ec2-results-low-mr"
echo export dynamodb_metadata_table="neardata-test-table"
echo export execution_mode="EC2"
echo export pipeline_type="Salmon"
echo export start_cwagent="True"
} >> /etc/environment

su ubuntu -c "python3 /opt/TAtlas/Consumer/consumer.py"
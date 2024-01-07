#!/usr/bin/env bash
#/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -a fetch-config -m ec2 -c ssm:ec2_cwagent_config -s
aws s3 sync s3://neardata-src/source/STAR/ /opt/TAtlas

{
echo export queue_name="STAR_queue"
echo export s3_bucket_name="transcriptomics-atlas"
echo export dynamodb_metadata_table="neardata-test-table"
echo export execution_mode="EC2"
echo export pipeline_type="STAR"
} >> /etc/environment

su ubuntu -c "mkdir /opt/TAtlas/STAR_data/STAR_index_mount"
aws ec2 attach-volume --instance-id="$(wget -q -O - http://169.254.169.254/latest/meta-data/instance-id)" --volume-id=vol-0de5339b3c119e2eb --region=us-east-1 --device=/dev/sdf
sleep 10
mount /dev/nvme1n1 /opt/TAtlas/STAR_data/STAR_index_mount/

su ubuntu -c "python3 /opt/TAtlas/Consumer/consumer.py"
#!/usr/bin/env bash
#/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -a fetch-config -m ec2 -c ssm:ec2_cwagent_config -s
# rm -rf because sync below is unreliable
rm -rf /opt/TAtlas/Consumer /opt/TAtlas/DESeq2
aws s3 sync s3://neardata-src/source/Salmon /opt/TAtlas

{
echo export queue_name="Salmon_queue"
echo export s3_bucket_name="transcriptomics-atlas"
echo export dynamodb_metadata_table="transcriptomics-atlas-salmon-metadata"
echo export execution_mode="EC2"
echo export pipeline_type="Salmon"
echo export index_release="111"
} >> /etc/environment

su ubuntu -c "python3 /opt/TAtlas/Consumer/consumer.py"
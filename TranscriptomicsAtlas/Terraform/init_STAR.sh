#!/usr/bin/env bash
#/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -a fetch-config -m ec2 -c ssm:ec2_cwagent_config -s
#/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -m ec2 -a stop
# rm -rf because sync below is unreliable
rm -rf /opt/TAtlas/Consumer /opt/TAtlas/DESeq2
aws s3 sync s3://neardata-src/source/STAR/ /opt/TAtlas

{
echo export queue_name="STAR_queue"
echo export s3_bucket_name="neardata-star-ec2-results"
echo export dynamodb_metadata_table="neardata-test-table"
echo export execution_mode="EC2"
echo export pipeline_type="STAR"
echo export index_release="111"
} >> /etc/environment

mkdir /opt/TAtlas/STAR_data/STAR_index_mount -p
aws ec2 attach-volume --instance-id="$(wget -q -O - http://169.254.169.254/latest/meta-data/instance-id)" --volume-id=vol-0413899b97d48c54f --region=us-east-1 --device=/dev/sdf
sleep $((5 + RANDOM % 10))
mount /dev/nvme1n1 /opt/TAtlas/STAR_data/STAR_index_mount/

mkdir /opt/TAtlas/STAR_data/STAR_index/STAR_index_hg38_gtf_release_111 -p
cp /opt/TAtlas/STAR_data/STAR_index_mount/STAR_index_hg38_gtf_release_111/ /opt/TAtlas/STAR_data/STAR_index/ -r

umount /opt/TAtlas/STAR_data/STAR_index_mount/
aws ec2 detach-volume --instance-id="$(wget -q -O - http://169.254.169.254/latest/meta-data/instance-id)" --volume-id=vol-0413899b97d48c54f --region=us-east-1 --device=/dev/sdf

su ubuntu -c "python3 /opt/TAtlas/Consumer/consumer.py"
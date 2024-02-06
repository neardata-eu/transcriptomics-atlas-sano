import os

import boto3
from moto import mock_aws

from config import sra_dir, fastq_dir, salmon_dir, deseq2_dir
from utils import clean_dir


@mock_aws
class BaseCase:
    def setup_method(self, method):
        s3 = boto3.resource("s3", region_name="us-east-1")
        sqs = boto3.resource("sqs", region_name="us-east-1")
        dynamodb_resource = boto3.resource('dynamodb', region_name="us-east-1")

        # CREATE RESOURCES
        self.bucket = s3.create_bucket(Bucket=os.environ["s3_bucket_name"])
        self.queue = sqs.create_queue(QueueName=os.environ["queue_name"])
        self.table = dynamodb_resource.create_table(
            TableName=os.environ["dynamodb_metadata_table"],
            KeySchema=[{'AttributeName': 'SRR_id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'SRR_id', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )

    def teardown_method(self, method):
        self.queue.delete()
        self.bucket.objects.all().delete()
        self.table.delete()
        for directory in [sra_dir, fastq_dir, salmon_dir, deseq2_dir]:
            clean_dir(directory)

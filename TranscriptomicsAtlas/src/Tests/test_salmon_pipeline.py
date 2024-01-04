import os
import unittest

import boto3
from moto import mock_sqs, mock_dynamodb, mock_s3, mock_logs

from consumer import start_pipeline
from utils import PipelineError, clean_dir
from config import sra_dir, fastq_dir, salmon_dir, deseq2_dir
from pipeline_steps import prefetch, fasterq_dump, salmon, deseq2_salmon


@mock_s3
@mock_sqs
@mock_logs
@mock_dynamodb
class TestUtils(unittest.TestCase):
    queue = None

    def setUp(self):
        ## CREATE BUCKETS
        s3 = boto3.resource("s3", region_name="us-east-1")
        self.salmon_bucket = s3.create_bucket(Bucket=os.environ["s3_bucket_name"])
        self.salmon_low_mr_bucket = s3.create_bucket(Bucket=os.environ["s3_bucket_name_low_mr"])

        ## CREATE SQS QUEUE
        queue_name = os.environ["queue_name"]
        sqs = boto3.resource("sqs", region_name="us-east-1")
        sqs.create_queue(QueueName=queue_name)
        self.queue = sqs.get_queue_by_name(QueueName=queue_name)

        ## CREATE DYNAMODB TABLE
        dynamodb_resource = boto3.resource('dynamodb', region_name="us-east-1")
        table_name = os.environ["dynamodb_metadata_table"]
        self.table = dynamodb_resource.create_table(
            TableName=table_name,
            KeySchema=[
                {
                    'AttributeName': 'SRR_id',
                    'KeyType': 'HASH'
                },
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'SRR_id',
                    'AttributeType': 'S'
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )

    def tearDown(self):
        self.queue.delete()
        self.salmon_bucket.objects.all().delete()
        self.salmon_low_mr_bucket.objects.all().delete()
        self.table.delete()
        for directory in [sra_dir, fastq_dir, salmon_dir, deseq2_dir]:
            clean_dir(directory)

    def test_sqs(self):
        messages = ["kidney_cells-SRR13210228"]
        entries = [{"Id": srr_id, "MessageBody": srr_id} for srr_id in messages]
        self.queue.send_messages(Entries=entries)

        msg_back = self.queue.receive_messages(MaxNumberOfMessages=1, WaitTimeSeconds=5)[0]
        srr_id = msg_back.body

        assert messages[0] == srr_id

    def test_s3(self):
        with open("test_normalized_counts.txt", "w+") as f:
            f.write("test")
        self.salmon_bucket.Object(f"test.txt").upload_file('test_normalized_counts.txt')
        self.salmon_bucket.Object(f"test.txt").load()

    def run_pipeline(self, tissue_name, srr_id):
        ## SEND MESSAGE
        entries = [{"Id": srr_id, "MessageBody": f"{tissue_name}-{srr_id}"}]
        self.queue.send_messages(Entries=entries)

        ## START PIPELINE
        start_pipeline(mode="job")

    def test_pipeline(self):
        tissue_name = "kidney_cells"
        srr_id = "SRR13210228"

        self.run_pipeline(tissue_name, srr_id)

        ## CHECK S3 AND DYNAMODB
        self.salmon_low_mr_bucket.Object(f"{tissue_name}/{srr_id}_normalized_counts.txt").load()
        assert "Item" in self.table.get_item(Key={"SRR_id": srr_id})
        print(self.table.get_item(Key={"SRR_id": srr_id}))

    def test_prefetch_big_sra_file(self):
        srr_id = "SRR13179686"  # 37 GB in size

        with self.assertRaises(PipelineError):
            prefetch(srr_id)

    def test_prefetch(self):
        prefetch("SRR13210228")

        assert os.path.exists(f"{sra_dir}/SRR13210228.sra")

    def test_fasterq_dump(self):
        prefetch("SRR13210228")
        fasterq_dump("SRR13210228")

        assert os.path.exists(f"{sra_dir}/SRR13210228.sra")

    def test_salmon(self):
        prefetch("SRR13210228")
        fasterq_dump("SRR13210228")
        salmon("SRR13210228", metadata={})

    def test_deseq2(self):
        prefetch("SRR13210228")
        fasterq_dump("SRR13210228")
        salmon("SRR13210228", metadata={})
        deseq2_salmon("SRR13210228")

    def test_skipping_processed_sra_ids(self):
        tissue_name = "kidney_cells"
        srr_id = "SRR13210228"

        item = {"SRR_id": srr_id}
        self.table.put_item(Item=item)
        entries = [{"Id": srr_id, "MessageBody": f"{tissue_name}-{srr_id}"}]
        self.queue.send_messages(Entries=entries)

        start_pipeline(mode="job")

        assert item == (self.table.get_item(Key={"SRR_id": srr_id}))["Item"]

    def test_clean_dirs(self):
        tissue_name = "kidney_cells"
        srr_id = "SRR13210228"

        self.run_pipeline(tissue_name, srr_id)

        for directory in [sra_dir, fastq_dir, salmon_dir, deseq2_dir]:
            assert not os.listdir(directory)


if __name__ == "__main__":
    unittest.main()

import os
import json
from decimal import Decimal
from datetime import datetime

import boto3

from config import nproc, metadata_dir, sra_dir, fastq_dir, salmon_dir, deseq2_dir
from pipeline_steps import prefetch, fasterq_dump, salmon, deseq2
from aws_utils import get_instance_id, srr_id_in_metadata_table
from logger import logger
from utils import clean_dir, nested_dict

logger.info(f"Nproc={nproc}")


class SalmonPipeline:
    metadata = nested_dict()
    tissue_name: str
    srr_id: str

    # AWS
    s3 = boto3.resource('s3')
    metadata_table = boto3.resource('dynamodb').Table(os.environ["dynamodb_metadata_table"])
    s3_bucket_name = os.environ["s3_bucket_name"]
    s3_bucket_name_low_mr = os.environ["s3_bucket_name_low_mr"]

    def __init__(self, message):
        self.tissue_name, self.srr_id = message.split("-")

    def start(self):
        if self.check_if_file_already_processed():
            return

        self.make_timestamps(
            prefetch, self.srr_id
        )

        self.make_timestamps(
            fasterq_dump, self.srr_id
        )

        self.make_timestamps(
            salmon, self.srr_id, self.metadata
        )

        self.make_timestamps(
            deseq2, self.srr_id
        )

        self.upload_normalized_counts_to_s3()
        self.gather_metadata()
        self.upload_metadata()

    def check_if_file_already_processed(self):
        logger.info("Checking if the pipeline has already been run.")
        if not srr_id_in_metadata_table(self.metadata_table, self.srr_id):
            logger.info("SRR_id not found in metadata table, starting the pipeline")
            return False
        else:
            logger.info("SRR_id found in metadata table, skipping.")
            return True

    def make_timestamps(self, pipeline_func, *args, **kwargs):
        self.metadata[pipeline_func.__name__ + "_start_time"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        pipeline_func(*args, **kwargs)
        self.metadata[pipeline_func.__name__ + "_end_time"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    def upload_normalized_counts_to_s3(self):
        logger.info("S3 upload starting")
        bucket = self.s3_bucket_name if self.metadata["salmon_mapping_rate [%]"] >= 30 else self.s3_bucket_name_low_mr
        self.s3.meta.client.upload_file(f'{deseq2_dir}/{self.srr_id}_normalized_counts.txt', bucket,
                                        f"{self.tissue_name}/{self.srr_id}_normalized_counts.txt")
        self.metadata["bucket"] = bucket
        logger.info("S3 upload finished")

    def gather_metadata(self):
        logger.info("Measuring file sizes")
        srr_filesize = os.stat(f"{sra_dir}/{self.srr_id}.sra").st_size
        if os.path.exists(f"{fastq_dir}/{self.srr_id}.fastq"):
            fastq_filesize = os.stat(f"{fastq_dir}/{self.srr_id}.fastq").st_size
        else:
            fastq_filesize = os.stat(f"{fastq_dir}/{self.srr_id}_1.fastq").st_size + \
                             os.stat(f"{fastq_dir}/{self.srr_id}_2.fastq").st_size

        self.metadata["SRR_id"] = self.srr_id
        self.metadata["tissue_name"] = self.tissue_name
        self.metadata["instance_id"] = get_instance_id()
        self.metadata["SRR_filesize_bytes"] = srr_filesize
        self.metadata["fastq_filesize_bytes"] = fastq_filesize
        self.metadata["execution_mode"] = os.environ["execution_mode"]

        logger.info("Saving metadata")
        with open(f'{metadata_dir}/{self.srr_id}_metadata.json', "w+") as f:
            json.dump(self.metadata, f, indent=4)

    def upload_metadata(self):
        logger.info("DynamoDB upload metadata starting")
        item = json.loads(json.dumps(self.metadata), parse_float=Decimal)
        self.metadata_table.put_item(Item=item)
        logger.info("DynamoDB upload metadata finished")

    def clean(self):
        logger.info("Starting removing generated files")
        for directory in [sra_dir, fastq_dir, salmon_dir, deseq2_dir]:
            clean_dir(directory)
        logger.info("Finished removing generated files")


def process_messages(messages):
    for message in messages:
        logger.info(f"Received msg={message.body}")
        try:
            pipeline = SalmonPipeline(message.body)
            pipeline.start()
        except Exception as e:
            logger.warning(e)
        finally:
            pipeline.clean()
        message.delete()
        logger.info("Processed and deleted msg. Awaiting next one")


def start_pipeline(mode="job"):
    try:
        queue = boto3.resource("sqs").get_queue_by_name(QueueName=os.environ["queue_name"])
        logger.info("Awaiting messages")
        if mode == "job":
            messages = queue.receive_messages(MaxNumberOfMessages=1, WaitTimeSeconds=5)
            process_messages(messages)
        elif mode == "server":
            while True:
                messages = queue.receive_messages(MaxNumberOfMessages=1, WaitTimeSeconds=5)
                process_messages(messages)
    except Exception as e:
        logger.warning(e)


if __name__ == "__main__":
    start_pipeline(mode="server")

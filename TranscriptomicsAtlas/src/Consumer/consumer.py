import os
import json
import subprocess
from datetime import datetime

import boto3

from logger import logger, log_output
from utils import clean_dir, nested_dict
from aws_utils import get_ssm_parameter, get_sqs_queue, get_instance_id, check_file_exists

my_env = {**os.environ, 'PATH': '/home/ubuntu/sratoolkit/sratoolkit.3.0.1-ubuntu64/bin:'
                                '/home/ubuntu/salmon-latest_linux_x86_64/bin:' + os.environ['PATH']}
work_dir = "/home/ubuntu"

nproc = subprocess.run(["nproc", "--all"], capture_output=True, text=True).stdout.strip()


@log_output
def prefetch(srr_id):
    prefetch_result = subprocess.run(
        ["prefetch", srr_id],
        capture_output=True, text=True, env=my_env, cwd=work_dir
    )
    return prefetch_result


@log_output
def fasterq_dump(srr_id, fastq_dir):
    fasterq_result = subprocess.run(
        ["fasterq-dump", srr_id, "--outdir", fastq_dir, "--threads", nproc],
        capture_output=True, text=True, env=my_env, cwd=work_dir
    )
    return fasterq_result


@log_output
def salmon(srr_id, fastq_dir):
    index_path = "/home/ubuntu/index/human_transcriptome_index"
    quant_dir = f"/home/ubuntu/salmon/{srr_id}"
    os.makedirs(quant_dir, exist_ok=True)

    salmon_result = subprocess.run(
        ["salmon", "quant", "--threads", nproc, "--useVBOpt", "-i", index_path, "-l", "A",
         "-1", f"{fastq_dir}/{srr_id}_1.fastq", "-2", f"{fastq_dir}/{srr_id}_2.fastq", "-o", quant_dir],
        capture_output=True, text=True, env=my_env, cwd=work_dir
    )
    return salmon_result


@log_output
def deseq2(srr_id):
    deseq2_result = subprocess.run(
        ["Rscript", "/home/ubuntu/DESeq2/count_normalization.R", srr_id],
        capture_output=True, text=True, env=my_env, cwd=work_dir
    )
    return deseq2_result


class SalmonPipeline:
    srr_id: str
    fastq_dir: str
    metadata_dir: str = "/home/ubuntu/metadata"
    metadata = nested_dict()

    s3 = boto3.resource('s3')
    s3_bucket_name = get_ssm_parameter(param_name="/neardata/s3_bucket_name")
    s3_metadata_bucket_name = get_ssm_parameter(param_name="/neardata/s3_bucket_metadata_name")

    def __init__(self, srr_id):
        self.srr_id = srr_id
        self.fastq_dir = f"/home/ubuntu/fastq/{self.srr_id}"
        os.makedirs(self.metadata_dir, exist_ok=True)
        os.makedirs(self.fastq_dir, exist_ok=True)

    def start(self):
        if self.check_if_results_exist_in_s3():
            return

        self.make_timestamps(
            prefetch, self.srr_id
        )

        self.make_timestamps(
            fasterq_dump, self.srr_id, self.fastq_dir
        )

        self.make_timestamps(
            salmon, self.srr_id, self.fastq_dir
        )

        self.make_timestamps(
            deseq2, self.srr_id
        )

        self.upload_normalized_counts_to_s3()
        self.gather_metadata()
        self.upload_metadata()
        self.clean()

    def check_if_results_exist_in_s3(self):
        logger.info("Checking if the pipeline has already been run")
        path_to_file = f'normalized_counts/{self.srr_id}/{self.srr_id}_normalized_counts.txt'
        if not check_file_exists(self.s3_bucket_name, path_to_file):
            logger.info("File not found, starting the pipeline")
            return False
        else:
            logger.info("Results exist in S3 bucket, exiting")
            return True

    def make_timestamps(self, pipeline_func, *args, **kwargs):
        self.metadata["timestamps"][pipeline_func.__name__]["start_time"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        pipeline_func(*args, **kwargs)
        self.metadata["timestamps"][pipeline_func.__name__]["end_time"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    def upload_normalized_counts_to_s3(self):
        logger.info("S3 upload starting")
        self.s3.meta.client.upload_file(f'/home/ubuntu/R_output/{self.srr_id}_normalized_counts.txt', self.s3_bucket_name,
                                   f"normalized_counts/{self.srr_id}/{self.srr_id}_normalized_counts.txt")
        logger.info("S3 upload finished")

    def gather_metadata(self):
        logger.info("Measuring file sizes")
        srr_filesize = os.stat(f"/home/ubuntu/sratoolkit/local/sra/{self.srr_id}.sra").st_size
        fastq_filesize = os.stat(f"{self.fastq_dir}/{self.srr_id}_1.fastq").st_size + \
                         os.stat(f"{self.fastq_dir}/{self.srr_id}_2.fastq").st_size

        self.metadata["instance_id"] = get_instance_id()
        self.metadata["SRR_id"] = self.srr_id
        self.metadata["SRR_filesize_bytes"] = srr_filesize
        self.metadata["fastq_filesize_bytes"] = fastq_filesize

        logger.info("Saving metadata")
        with open(f'{self.metadata_dir}/{self.srr_id}_metadata.json', "w+") as f:
            json.dump(self.metadata, f, indent=4)

    def upload_metadata(self):
        logger.info("S3 upload metadata starting")
        self.s3.meta.client.upload_file(f'{self.metadata_dir}/{self.srr_id}_metadata.json',
                                        self.s3_metadata_bucket_name,
                                        f"{self.srr_id}/{self.srr_id}_metadata.json")
        logger.info("S3 upload metadata finished")

    def clean(self):
        logger.info("Starting removing generated files")
        clean_dir("/home/ubuntu/sratoolkit/local/sra")
        clean_dir("/home/ubuntu/fastq")
        clean_dir("/home/ubuntu/salmon")
        clean_dir("/home/ubuntu/R_output")
        logger.info("Finished removing generated files")


if __name__ == "__main__":
    queue = get_sqs_queue()
    logger.info("Awaiting messages")
    while True:
        messages = queue.receive_messages(MaxNumberOfMessages=1, WaitTimeSeconds=5)
        for message in messages:
            logger.info(f"Received msg={message.body}")
            SalmonPipeline(message.body).start()
            message.delete()
            logger.info("Processed and deleted msg. Awaiting next one")

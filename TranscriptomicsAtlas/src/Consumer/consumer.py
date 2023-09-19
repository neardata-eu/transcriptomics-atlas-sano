import os
import re
import json
import subprocess
from decimal import Decimal
from datetime import datetime

import boto3
import backoff

from aws_utils import get_instance_id, srr_id_in_metadata_table
from logger import logger, log_output
from utils import clean_dir, nested_dict, PipelineError

my_env = {**os.environ, 'PATH': '/opt/TAtlas/sratoolkit.3.0.1-ubuntu64/bin:'
                                '/opt/TAtlas/salmon-latest_linux_x86_64/bin:' + os.environ['PATH']}
work_dir = "/home/ubuntu/TAtlas"

nproc = subprocess.run(["nproc"], capture_output=True, text=True).stdout.strip()
logger.info(f"Nproc={nproc}")


@backoff.on_exception(backoff.constant, PipelineError, max_tries=2, logger=logger)
@log_output
def prefetch(srr_id):
    prefetch_result = subprocess.run(
        ["prefetch", srr_id],
        capture_output=True, text=True, env=my_env, cwd=work_dir
    )
    return prefetch_result


@backoff.on_exception(backoff.constant, PipelineError, max_tries=2, logger=logger)
@log_output
def fasterq_dump(srr_id, fastq_dir):
    fasterq_result = subprocess.run(
        ["fasterq-dump", srr_id, "--outdir", fastq_dir, "--threads", nproc],
        capture_output=True, text=True, env=my_env, cwd=work_dir
    )
    return fasterq_result


@log_output
def salmon(srr_id, fastq_dir, metadata):
    index_path = "/opt/TAtlas/salmon_index/"
    quant_dir = f"/home/ubuntu/TAtlas/salmon/{srr_id}"
    os.makedirs(quant_dir, exist_ok=True)

    if os.path.exists(f"{fastq_dir}/{srr_id}.fastq"):
        salmon_result = subprocess.run(
            ["salmon", "quant", "--threads", nproc, "--useVBOpt", "-i", index_path, "-l", "A",
             "-r", f"{fastq_dir}/{srr_id}.fastq", "-o", quant_dir],
            capture_output=True, text=True, env=my_env, cwd=work_dir
        )
    else:
        salmon_result = subprocess.run(
            ["salmon", "quant", "--threads", nproc, "--useVBOpt", "-i", index_path, "-l", "A",
             "-1", f"{fastq_dir}/{srr_id}_1.fastq", "-2", f"{fastq_dir}/{srr_id}_2.fastq", "-o", quant_dir],
            capture_output=True, text=True, env=my_env, cwd=work_dir
        )

    salmon_output = salmon_result.stderr
    if "Found no concordant and consistent mappings." in salmon_output:
        raise PipelineError(f"Found no concordant and consistent mappings for {srr_id}. Aborting the pipeline.")

    pattern = r'Mapping rate = (.*)%'
    match = re.search(pattern, salmon_output)
    if match:
        mapping_rate = float(match.group(1))
    else:
        raise PipelineError("Mapping rate not found. Aborting the pipeline.")

    metadata["salmon_mapping_rate [%]"] = mapping_rate

    return salmon_result


@log_output
def deseq2(srr_id):
    deseq2_result = subprocess.run(
        ["Rscript", "/opt/TAtlas/DESeq2/count_normalization.R", srr_id],
        capture_output=True, text=True, env=my_env, cwd=work_dir
    )
    return deseq2_result


class SalmonPipeline:
    srr_id: str
    tissue_name: str
    fastq_dir: str
    metadata_dir: str = "/home/ubuntu/TAtlas/metadata"
    metadata = nested_dict()

    s3 = boto3.resource('s3')
    metadata_table = boto3.resource('dynamodb').Table(os.environ["dynamodb_metadata_table"])
    s3_bucket_name = os.environ["s3_bucket_name"]
    s3_bucket_name_low_mr = os.environ["s3_bucket_name_low_mr"]

    def __init__(self, message):
        self.tissue_name, self.srr_id = message.split("-")
        self.fastq_dir = f"/home/ubuntu/TAtlas/fastq/{self.srr_id}"
        os.makedirs(self.metadata_dir, exist_ok=True)
        os.makedirs(self.fastq_dir, exist_ok=True)

    def start(self):
        if self.check_if_file_already_processed():
            return

        self.make_timestamps(
            prefetch, self.srr_id
        )

        self.make_timestamps(
            fasterq_dump, self.srr_id, self.fastq_dir
        )

        self.make_timestamps(
            salmon, self.srr_id, self.fastq_dir, self.metadata
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
        self.metadata[pipeline_func.__name__+"_start_time"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        pipeline_func(*args, **kwargs)
        self.metadata[pipeline_func.__name__+"_end_time"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    def upload_normalized_counts_to_s3(self):
        logger.info("S3 upload starting")
        if self.metadata["salmon_mapping_rate [%]"] >= 30:
            self.s3.meta.client.upload_file(f'/home/ubuntu/TAtlas/R_output/{self.srr_id}_normalized_counts.txt',
                                            self.s3_bucket_name,
                                            f"{self.tissue_name}/{self.srr_id}_normalized_counts.txt")
            self.metadata["bucket"] = self.s3_bucket_name
        else:
            self.s3.meta.client.upload_file(f'/home/ubuntu/TAtlas/R_output/{self.srr_id}_normalized_counts.txt',
                                            self.s3_bucket_name_low_mr,
                                            f"{self.tissue_name}/{self.srr_id}_normalized_counts.txt")
            self.metadata["bucket"] = self.s3_bucket_name_low_mr
        logger.info("S3 upload finished")

    def gather_metadata(self):
        logger.info("Measuring file sizes")
        srr_filesize = os.stat(f"/home/ubuntu/TAtlas/sratoolkit/sra/{self.srr_id}.sra").st_size
        if os.path.exists(f"{self.fastq_dir}/{self.srr_id}.fastq"):
            fastq_filesize = os.stat(f"{self.fastq_dir}/{self.srr_id}.fastq").st_size
        else:
            fastq_filesize = os.stat(f"{self.fastq_dir}/{self.srr_id}_1.fastq").st_size + \
                             os.stat(f"{self.fastq_dir}/{self.srr_id}_2.fastq").st_size

        self.metadata["SRR_id"] = self.srr_id
        self.metadata["tissue_name"] = self.tissue_name
        self.metadata["instance_id"] = get_instance_id()
        self.metadata["SRR_filesize_bytes"] = srr_filesize
        self.metadata["fastq_filesize_bytes"] = fastq_filesize
        self.metadata["execution_mode"] = "EC2" if "RUN_IN_CONTAINER" not in os.environ else "Container"

        logger.info("Saving metadata")
        with open(f'{self.metadata_dir}/{self.srr_id}_metadata.json', "w+") as f:
            json.dump(self.metadata, f, indent=4)

    def upload_metadata(self):
        logger.info("DynamoDB upload metadata starting")
        item = json.loads(json.dumps(self.metadata), parse_float=Decimal)
        self.metadata_table.put_item(Item=item)
        logger.info("DynamoDB upload metadata finished")

    def clean(self):
        logger.info("Starting removing generated files")
        clean_dir("/home/ubuntu/TAtlas/sratoolkit")
        clean_dir("/home/ubuntu/TAtlas/fastq")
        clean_dir("/home/ubuntu/TAtlas/salmon")
        clean_dir("/home/ubuntu/TAtlas/R_output")
        logger.info("Finished removing generated files")


if __name__ == "__main__":
    queue = boto3.resource("sqs").get_queue_by_name(QueueName=os.environ["queue_name"])
    logger.info("Awaiting messages")
    while True:
        messages = queue.receive_messages(MaxNumberOfMessages=1, WaitTimeSeconds=5)
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

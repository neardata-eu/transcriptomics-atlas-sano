import os
import json
import subprocess

import boto3
import botocore
import requests
import watchtower, logging
from datetime import datetime
from collections import defaultdict
from functools import wraps

nested_dict = lambda: defaultdict(nested_dict)  # NOQA
my_env = {**os.environ, 'PATH': '/home/ubuntu/sratoolkit/sratoolkit.3.0.1-ubuntu64/bin:'
                                '/home/ubuntu/salmon-latest_linux_x86_64/bin:' + os.environ['PATH']}
work_dir = "/home/ubuntu"

metadata_url = 'http://169.254.169.254/latest/meta-data/'
os.environ['AWS_DEFAULT_REGION'] = requests.get(metadata_url + 'placement/region').text
nproc = subprocess.run(["nproc", "--all"], capture_output=True, text=True).stdout.strip()
instance_id = requests.get(metadata_url + 'instance-id').text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.addHandler(watchtower.CloudWatchLogHandler(send_interval=1))

#  Retrieve queue_name from Parameter Store
ssm = boto3.client("ssm")
sqs = boto3.resource("sqs")
s3 = boto3.resource('s3')

queue_name_parameter = ssm.get_parameter(Name="/neardata/queue_name", WithDecryption=True)
queue_name = queue_name_parameter['Parameter']['Value']
queue = sqs.get_queue_by_name(QueueName=queue_name)

s3_bucket_parameter = ssm.get_parameter(Name="/neardata/s3_bucket_name", WithDecryption=True)
s3_bucket_name = s3_bucket_parameter['Parameter']['Value']
s3_bucket_metadata_parameter = ssm.get_parameter(Name="/neardata/s3_bucket_metadata_name", WithDecryption=True)
s3_bucket_metadata_name = s3_bucket_metadata_parameter['Parameter']['Value']


def clean_dir(path):
    for root, dirs, files in os.walk(path, topdown=False):
        for file_name in files:
            file_path = os.path.join(root, file_name)
            os.remove(file_path)
        for dir_name in dirs:
            dir_path = os.path.join(root, dir_name)
            os.rmdir(dir_path)
    logger.info(f"Removed files in {path}")


def log_output(func):
    @wraps(func)
    def with_logging(*args, **kwargs):
        logger.info(f"{func.__name__} started")

        result = func(*args, **kwargs)

        logger.info(result.stdout)
        logger.warning(result.stderr)
        if result.returncode != 0:
            logger.error(f"{func.__name__} failed, exiting")
            exit(1)
        logger.info(f"{func.__name__} finished")

        return result

    return with_logging


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


def consume_message(srr_id):
    metadata = nested_dict()
    ### Check if file exists in S3, if yes then skip ###
    try:  # TODO replace try-except with listing files?  https://stackoverflow.com/questions/33842944/check-if-a-key-exists-in-a-bucket-in-s3-using-boto3
        logger.info("Checking if the pipeline has already been run")
        s3.Object(s3_bucket_name, f'normalized_counts/{srr_id}/{srr_id}_normalized_counts.txt').load()
        logger.info("Results exist in S3 bucket, exiting")
        # return
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] != "404":
            logger.warning(e)
            return
        logger.info("File not found, starting the pipeline")

    ###  Downloading SRR file ###
    metadata["timestamps"]["1st_phase_prefetch"]["start_time"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    prefetch(srr_id)

    metadata["timestamps"]["1st_phase_prefetch"]["end_time"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    ###  Unpacking SRR to .fastq using fasterq-dump ###
    metadata["timestamps"]["2nd_phase_fasterq"]["start_time"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    fastq_dir = f"/home/ubuntu/fastq/{srr_id}"
    os.makedirs(fastq_dir, exist_ok=True)

    fasterq_dump(srr_id, fastq_dir)

    metadata["timestamps"]["2nd_phase_fasterq"]["end_time"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    ###  Quantification using Salmon ###
    metadata["timestamps"]["3rd_phase_salmon"]["start_time"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    salmon(srr_id, fastq_dir)

    metadata["timestamps"]["3rd_phase_salmon"]["end_time"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    ### Run R script on quant.sf
    # Update samples.txt script with correct SRR_ID
    metadata["timestamps"]["4th_phase_DESeq2"]["start_time"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    deseq2(srr_id)
    metadata["timestamps"]["4th_phase_DESeq2"]["end_time"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    ### Upload normalized counts to S3 ###
    logger.info("S3 upload starting")
    s3.meta.client.upload_file(f'/home/ubuntu/R_output/{srr_id}_normalized_counts.txt', s3_bucket_name,
                               f"normalized_counts/{srr_id}/{srr_id}_normalized_counts.txt")
    logger.info("S3 upload finished")

    # Metadata and upload
    logger.info("Measuring file sizes")
    srr_filesize = os.stat(f"/home/ubuntu/sratoolkit/local/sra/{srr_id}.sra").st_size
    fastq_filesize = os.stat(f"{fastq_dir}/{srr_id}_1.fastq").st_size + os.stat(f"{fastq_dir}/{srr_id}_2.fastq").st_size

    metadata["instance_id"] = instance_id
    metadata["SRR_id"] = srr_id
    metadata["SRR_filesize_bytes"] = srr_filesize
    metadata["fastq_filesize_bytes"] = fastq_filesize

    logger.info("Saving metadata")
    metadata_dir = "/home/ubuntu/metadata"
    os.makedirs(metadata_dir, exist_ok=True)
    with open(f'{metadata_dir}/{srr_id}_metadata.json', "w+") as f:
        json.dump(metadata, f, indent=4)

    logger.info("S3 upload metadata starting")
    s3.meta.client.upload_file(f'{metadata_dir}/{srr_id}_metadata.json', s3_bucket_metadata_name,
                               f"{srr_id}/{srr_id}_metadata.json")
    logger.info("S3 upload metadata finished")


if __name__ == "__main__":
    logger.info("Awaiting messages")
    while True:
        messages = queue.receive_messages(MaxNumberOfMessages=1,
                                          WaitTimeSeconds=5)  # TODO check if message is indeed SRA id
        for message in messages:
            logger.info(f"Received msg={message.body}")
            consume_message(message.body)
            message.delete()

            ### Clean all input and output files ###
            logger.info("Starting removing generated files")
            clean_dir("/home/ubuntu/sratoolkit/local/sra")
            clean_dir("/home/ubuntu/fastq")
            clean_dir("/home/ubuntu/salmon")
            clean_dir("/home/ubuntu/R_output")
            logger.info("Finished removing generated files")

            logger.info("Processed and deleted msg. Awaiting next one")

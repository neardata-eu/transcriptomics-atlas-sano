import os
import subprocess
from time import sleep
from pathlib import Path

import requests

import boto3
import botocore

#  TODO is this really necessary?
metadata_url = 'http://169.254.169.254/latest/meta-data/'
os.environ['AWS_DEFAULT_REGION'] = requests.get(metadata_url + 'placement/region').text

#  Retrieve queue_name from Parameter Store
ssm = boto3.client("ssm")
queue_name_paramter = ssm.get_parameter(Name="/neardata/queue_name", WithDecryption=True)
queue_name = queue_name_paramter['Parameter']['Value']

s3_bucket_paramter = ssm.get_parameter(Name="/neardata/s3_bucket_name", WithDecryption=True)
s3_bucket_name = s3_bucket_paramter['Parameter']['Value']

sqs = boto3.resource("sqs")
queue = sqs.get_queue_by_name(QueueName=queue_name)

s3 = boto3.resource('s3')


def consume_message(msg_body):
    srr_id = msg_body
    ### Check if file exists in S3, if yes then skip

    try:  # TODO replace try-except with listing files?  https://stackoverflow.com/questions/33842944/check-if-a-key-exists-in-a-bucket-in-s3-using-boto3
        print("Checking if the pipeline has already been run")
        s3.Object("neardata-bucket-123", f'normalized_counts/{srr_id}/{srr_id}_normalized_counts2.txt').load()
        print("File exisits, exiting")
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] != "404":
            print(e)
            return
        print("File not found, starting the pipeline")

    ###  Downloading SRR file ###            # TODO extract each step to separate function?
    print(f"Starting prefetch of {srr_id}")  # TODO replace print with logging
    # subprocess.run(
    #     [f"prefetch", msg_body]  #  TODO replace with S3 cpy if file available in bucket
    # )
    print(f"Prefetched")

    ###  Unpacking SRR to .fastq using fasterq-dump ###
    fastq_dir = f"/home/ubuntu/fastq/{srr_id}"
    os.makedirs(fastq_dir, exist_ok=True)  # TODO exist_ok=True? for now
    print("Starting unpacking the SRR file using fasterq-dump")
    # subprocess.run(
    #     ["fasterq-dump", srr_id, "--outdir", fastq_dir]
    # )
    print("Unpacking finished")

    ###  Quantification using Salmon ###
    index_path = "/home/ubuntu/index/human_transcriptome_index"
    quant_dir = f"/home/ubuntu/salmon/{srr_id}"
    os.makedirs(quant_dir, exist_ok=True)
    print("Quantification starting")
    # subprocess.run(
    #     ["salmon", "quant", "-p", "2", "--useVBOpt", "-i", index_path, "-l", "A", "-1", f"{fastq_dir}_1.fastq", "-2",
    #      f"{fastq_dir}_2.fastq", "-o", quant_dir]  # TODO check args
    # )
    # sleep(30)
    print("Quantification finished")

    ### Run R script on quant.sf
    print("DESeq2 starting")
    subprocess.run(
        ["Rscript", "DESeq2/salmon_to_deseq.R", srr_id]
    )
    print("DESeq2 finished")

    ### Upload normalized counts to S3 ###
    print("S3 upload starting")
    s3.meta.client.upload_file(f'/home/ubuntu/R_output/{srr_id}_normalized_counts.txt', s3_bucket_name,
                               f"normalized_counts/{srr_id}/{srr_id}_normalized_counts.txt")
    print("S3 upload finished")

    ### Clean all input and output files ###
    def clean_dir(path):
        for f in Path(path).glob("*"):
            if f.is_file():
                f.unlink()

    print("Starting removing R files")
    clean_dir("/home/ubuntu/R_output")
    print("Finished removing R files")


if __name__ == "__main__":
    print("Awaiting messages")
    while True:
        messages = queue.receive_messages(MaxNumberOfMessages=1)  # TODO check args
        for message in messages:
            print(f"Received msg={message.body}")
            consume_message(message.body)
            message.delete()
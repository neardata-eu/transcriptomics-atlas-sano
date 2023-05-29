import os
import subprocess

import boto3
import botocore
import requests
import watchtower, logging

my_env = {**os.environ, 'PATH': '/home/ubuntu/sratoolkit/sratoolkit.3.0.1-ubuntu64/bin:'
                                '/home/ubuntu/salmon-latest_linux_x86_64/bin:' + os.environ['PATH']}
work_dir = "/home/ubuntu"

metadata_url = 'http://169.254.169.254/latest/meta-data/'
os.environ['AWS_DEFAULT_REGION'] = requests.get(metadata_url + 'placement/region').text
nproc = subprocess.run(["nproc", "--all"], capture_output=True, text=True).stdout.strip()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.addHandler(watchtower.CloudWatchLogHandler(send_interval=1))

#  Retrieve queue_name from Parameter Store
ssm = boto3.client("ssm")
sqs = boto3.resource("sqs")
s3 = boto3.resource('s3')

queue_name_paramter = ssm.get_parameter(Name="/neardata/queue_name", WithDecryption=True)
queue_name = queue_name_paramter['Parameter']['Value']
queue = sqs.get_queue_by_name(QueueName=queue_name)

s3_bucket_paramter = ssm.get_parameter(Name="/neardata/s3_bucket_name", WithDecryption=True)
s3_bucket_name = s3_bucket_paramter['Parameter']['Value']


def clean_dir(path):
    for root, dirs, files in os.walk(path, topdown=False):
        for file_name in files:
            file_path = os.path.join(root, file_name)
            os.remove(file_path)
        for dir_name in dirs:
            dir_path = os.path.join(root, dir_name)
            os.rmdir(dir_path)
    logger.info(f"Removed files in {path}")


def consume_message(srr_id):
    ### Check if file exists in S3, if yes then skip ###
    try:  # TODO replace try-except with listing files?  https://stackoverflow.com/questions/33842944/check-if-a-key-exists-in-a-bucket-in-s3-using-boto3
        logger.info("Checking if the pipeline has already been run")
        s3.Object(s3_bucket_name, f'normalized_counts/{srr_id}/{srr_id}_normalized_counts.txt').load()
        logger.info("File exists, exiting")
        # return
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] != "404":
            logger.warning(e)
            return
        logger.info("File not found, starting the pipeline")

    ###  Downloading SRR file ###            # TODO extract each step to separate function?
    logger.info(f"Prefetch started")
    prefetch_result = subprocess.run(
        ["prefetch", srr_id],  # TODO test S3 cp performance if file available in bucket
        capture_output=True, text=True, env=my_env, cwd=work_dir
    )
    logger.info(prefetch_result.stdout)
    logger.warning(prefetch_result.stderr)
    if prefetch_result.returncode != 0:
        logger.error("Prefetch failed")
        exit(0)
    logger.info(f"Prefetch finished")

    ###  Unpacking SRR to .fastq using fasterq-dump ###
    fastq_dir = f"/home/ubuntu/fastq/{srr_id}"
    os.makedirs(fastq_dir, exist_ok=True)
    logger.info("Fasterq-dump started")
    fasterq_result = subprocess.run(
        ["fasterq-dump", srr_id, "--outdir", fastq_dir, "--threads", nproc],
        capture_output=True, text=True, env=my_env, cwd=work_dir
    )
    logger.info(fasterq_result.stdout)
    logger.warning(fasterq_result.stderr)
    if fasterq_result.returncode != 0:
        logger.error("Fasterq-dump failed")
        exit(0)
    logger.info("Fasterq-dump finished")

    ###  Quantification using Salmon ###
    index_path = "/home/ubuntu/index/human_transcriptome_index"
    quant_dir = f"/home/ubuntu/salmon/{srr_id}"
    os.makedirs(quant_dir, exist_ok=True)
    logger.info("SALMON starting")
    salmon_result = subprocess.run(
        ["salmon", "quant", "--threads", nproc, "--useVBOpt", "-i", index_path, "-l", "A",
         "-1", f"{fastq_dir}/{srr_id}_1.fastq", "-2", f"{fastq_dir}/{srr_id}_2.fastq", "-o", quant_dir],
        capture_output=True, text=True, env=my_env, cwd=work_dir
    )
    logger.info(salmon_result.stdout)
    logger.warning(salmon_result.stderr)
    if salmon_result.returncode != 0:
        logger.error("SALMON failed")
        exit(0)
    logger.info("SALMON finished")

    ### Run R script on quant.sf
    # Update samples.txt script with correct SRR_ID
    with open("/home/ubuntu/DESeq2/samples.txt", "w+") as f:
        f.write(f"""samples	pop	center	run	condition\n{srr_id}	1.1	HPC	{srr_id}	stimulus""")

    logger.info("DESeq2 starting")
    deseq2_result = subprocess.run(
        ["Rscript", "/home/ubuntu/DESeq2/count_normalization.R", srr_id],
        capture_output=True, text=True, env=my_env, cwd=work_dir
    )
    logger.info(deseq2_result.stdout)
    logger.warning(deseq2_result.stderr)
    if deseq2_result.returncode != 0:
        logger.error("DESeq2 failed")
        exit(0)
    logger.info("DESeq2 finished")

    ### Upload normalized counts to S3 ###
    logger.info("S3 upload starting")
    s3.meta.client.upload_file(f'/home/ubuntu/R_output/{srr_id}_normalized_counts.txt', s3_bucket_name,
                               f"normalized_counts/{srr_id}/{srr_id}_normalized_counts.txt")
    logger.info("S3 upload finished")


if __name__ == "__main__":
    logger.info("Awaiting messages")
    while True:
        messages = queue.receive_messages(MaxNumberOfMessages=1, WaitTimeSeconds=5)  # TODO check if message is indeed SRA id
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

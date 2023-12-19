import os
import time

import boto3
import requests

if os.environ["execution_mode"] == "EC2":
    os.environ['AWS_DEFAULT_REGION'] = requests.get('http://169.254.169.254/latest/meta-data/placement/region').text

from config import nproc
from logger import logger
from salmon_pipeline import SalmonPipeline
from utils import PipelineError

logger.info(f"Nproc={nproc}")


def process_messages(messages):
    for message in messages:
        logger.info(f"Received msg={message.body}")
        pipeline = SalmonPipeline(message.body)
        if pipeline.check_if_file_already_processed():
            continue

        try:
            pipeline.start()
        except PipelineError as e:
            logger.warning(e)
            pipeline.metadata["error_type"] = e.error_type
        finally:
            pipeline.gather_metadata()
            pipeline.upload_metadata()
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
            tries = 0
            max_tries = 15
            retry_interval = 5

            while tries < max_tries:
                messages = queue.receive_messages(MaxNumberOfMessages=1, WaitTimeSeconds=5)
                if len(messages) != 0:
                    process_messages(messages)
                    tries = 0
                else:
                    time.sleep(retry_interval)
                    tries += 1

            print("No more messages to consume. Exiting")

    except Exception as e:
        logger.warning(e)


if __name__ == "__main__":
    start_pipeline(mode="server")

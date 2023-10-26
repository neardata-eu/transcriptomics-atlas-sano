import os

import boto3

from config import nproc
from logger import logger
from salmon_pipeline import SalmonPipeline
from utils import PipelineError

logger.info(f"Nproc={nproc}")


def process_messages(messages):
    for message in messages:
        logger.info(f"Received msg={message.body}")
        pipeline = SalmonPipeline(message.body)
        try:
            pipeline.start()
        except PipelineError as e:
            logger.warning(e)
            pipeline.metadata["error_type"] = e.error_type
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

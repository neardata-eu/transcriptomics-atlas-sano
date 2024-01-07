import os
import logging
import watchtower

from functools import wraps

from aws_utils import get_instance_id
from utils import PipelineError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
log_stream_name = get_instance_id()+'/{program_name}/{logger_name}/{process_id}'
log_group_name = f"{os.environ['pipeline_type']}-{os.environ['execution_mode']}"
log_handler = watchtower.CloudWatchLogHandler(send_interval=1, log_group_name=log_group_name, log_stream_name=log_stream_name)
logger.addHandler(log_handler)


def log_output(func):
    @wraps(func)
    def with_logging(*args, **kwargs):
        logger.info(f"{func.__name__} started")

        result = func(*args, **kwargs)

        logger.info(result.stdout)
        logger.warning(result.stderr)
        if result.returncode != 0:
            raise PipelineError(f"{func.__name__} failed. Aborting the pipeline.", f"{func.__name__} failed")
        logger.info(f"{func.__name__} finished")

        return result

    return with_logging


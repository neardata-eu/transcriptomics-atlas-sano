import os
import logging
import watchtower

from functools import wraps

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.addHandler(watchtower.CloudWatchLogHandler(send_interval=1, log_stream_name=os.getenv('HOSTNAME')+'/{program_name}/{logger_name}/{process_id}'))


def log_output(func):
    @wraps(func)
    def with_logging(*args, **kwargs):
        logger.info(f"{func.__name__} started")

        result = func(*args, **kwargs)

        logger.info(result.stdout)
        logger.warning(result.stderr)
        if result.returncode != 0:
            err_msg = f"{func.__name__} failed. Aborting the pipeline."  # TODO Improve
            logger.error(err_msg)
            raise ValueError(err_msg)
        logger.info(f"{func.__name__} finished")

        return result

    return with_logging


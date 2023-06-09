import logging
import watchtower

from functools import wraps

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.addHandler(watchtower.CloudWatchLogHandler(send_interval=1))


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


import os
from collections import defaultdict

from logger import logger

nested_dict = lambda: defaultdict(nested_dict)  # NOQA


def clean_dir(path):
    for root, dirs, files in os.walk(path, topdown=False):
        for file_name in files:
            file_path = os.path.join(root, file_name)
            os.remove(file_path)
        for dir_name in dirs:
            dir_path = os.path.join(root, dir_name)
            os.rmdir(dir_path)
    logger.info(f"Removed files in {path}")

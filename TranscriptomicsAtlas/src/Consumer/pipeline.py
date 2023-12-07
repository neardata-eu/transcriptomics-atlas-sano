import os
import json
from decimal import Decimal
from datetime import datetime

import boto3

from aws_utils import srr_id_in_metadata_table, get_instance_id
from config import sra_dir, fastq_dir, metadata_dir
from logger import logger
from utils import nested_dict, PipelineError


class Pipeline:
    metadata = nested_dict()
    tissue_name: str
    srr_id: str

    metadata_table = boto3.resource('dynamodb').Table(os.environ["dynamodb_metadata_table"])

    def __init__(self, message):
        self.tissue_name, self.srr_id = message.split("-")

    def make_timestamps(self, pipeline_func, *args, **kwargs):
        self.metadata[pipeline_func.__name__ + "_start_time"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        pipeline_func(*args, **kwargs)
        self.metadata[pipeline_func.__name__ + "_end_time"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    def upload_metadata(self):
        logger.info("Metadata upload starting")
        item = json.loads(json.dumps(self.metadata), parse_float=Decimal)
        self.metadata_table.put_item(Item=item)
        logger.info("Metadata upload finished")

    def check_if_file_already_processed(self):
        logger.info("Checking if the pipeline has already been run.")
        if not srr_id_in_metadata_table(self.metadata_table, self.srr_id):
            logger.info("SRR_id not found in metadata table, starting the pipeline")
            return False
        else:
            logger.info("SRR_id found in metadata table, skipping.")
            return True

    def gather_metadata(self):
        logger.info("Gathering metadata")
        self.metadata["SRR_id"] = self.srr_id
        self.metadata["tissue_name"] = self.tissue_name
        self.metadata["instance_id"] = get_instance_id()
        self.metadata["execution_mode"] = os.environ["execution_mode"]
        self.metadata["SRR_filesize_bytes"] = self.measure_sra_size()
        self.metadata["fastq_filesize_bytes"] = self.measure_fastq_size()
        logger.info("Saving metadata")

        with open(f'{metadata_dir}/{self.srr_id}_metadata.json', "w+") as f:
            json.dump(self.metadata, f, indent=4)

    def measure_sra_size(self):
        sra_filepath = f"{sra_dir}/{self.srr_id}.sra"
        sra_filesize = "N/A"
        if os.path.exists(sra_filepath):
            sra_filesize = os.stat(sra_filepath).st_size

        return sra_filesize

    def measure_fastq_size(self):
        fastq_filepath_single = f"{fastq_dir}/{self.srr_id}.fastq"
        fastq_filepath_double_1 = f"{fastq_dir}/{self.srr_id}_1.fastq"
        fastq_filepath_double_2 = f"{fastq_dir}/{self.srr_id}_2.fastq"

        fastq_filesize = "N/A"
        # Handle two possible outcomes: either one fastq is generated or two.
        if os.path.exists(fastq_filepath_single):
            fastq_filesize = os.stat(fastq_filepath_single).st_size
        elif os.path.exists(fastq_filepath_double_1) and os.path.exists(fastq_filepath_double_2):
            fastq_filesize = os.stat(fastq_filepath_double_1).st_size + os.stat(fastq_filepath_double_2).st_size

        return fastq_filesize

    @staticmethod
    def validate_returncode(func_name, subprocess_result):
        logger.info(subprocess_result.stdout)
        logger.warning(subprocess_result.stderr)
        if subprocess_result.returncode != 0:
            raise PipelineError(f"{func_name} failed. Aborting the pipeline.", f"{func_name} failed")

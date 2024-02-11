import os

from config import sra_dir, fastq_dir, salmon_dir, deseq2_dir
from logger import logger
from pipeline import Pipeline
from pipeline_steps import prefetch, fasterq_dump, salmon, deseq2_salmon
from utils import clean_dir


class SalmonPipeline(Pipeline):
    def __init__(self, message):
        super().__init__(message)

    def start(self):
        self.make_timestamps(
            prefetch, self.srr_id
        )

        self.make_timestamps(
            fasterq_dump, self.srr_id, self.metadata
        )

        self.make_timestamps(
            salmon, self.srr_id, self.metadata
        )

        self.make_timestamps(
            deseq2_salmon, self.srr_id
        )

        self.upload_logs_to_s3()
        self.upload_counts_to_s3()

    def upload_counts_to_s3(self):
        logger.info("S3 upload counts starting")
        mr_folder = "high_mapping_rate" if self.metadata["salmon_mapping_rate [%]"] >= 30 else "low_mapping_rate"

        row_counts_local_path = f'{deseq2_dir}/{self.srr_id}/{self.srr_id}_salmon_row_counts.csv'
        normalized_counts_local_path = f'{deseq2_dir}/{self.srr_id}/{self.srr_id}_salmon_normalized_counts.txt'

        row_counts_s3_path = f"Salmon/{mr_folder}/{self.tissue_name}/row_counts/{self.srr_id}_salmon_row_counts.csv"
        normalized_counts_s3_path = f"Salmon/{mr_folder}/{self.tissue_name}/normalized_counts/{self.srr_id}_salmon_normalized_counts.txt"

        self.s3.meta.client.upload_file(row_counts_local_path, self.s3_bucket_name, row_counts_s3_path)
        self.s3.meta.client.upload_file(normalized_counts_local_path, self.s3_bucket_name, normalized_counts_s3_path)

        self.metadata["s3_path"] = f"s3://{self.s3_bucket_name}/{normalized_counts_s3_path}"
        logger.info("S3 upload counts finished")

    def upload_logs_to_s3(self):
        logger.info("S3 upload logs starting")
        mr_folder = "high_mapping_rate" if self.metadata["salmon_mapping_rate [%]"] >= 30 else "low_mapping_rate"

        final_logs_local_path = f"{salmon_dir}/{self.srr_id}/logs/salmon_quant.log"
        final_logs_s3_path = f"Salmon/{mr_folder}/{self.tissue_name}/logs/{self.srr_id}_salmon_quant.log"
        self.s3.meta.client.upload_file(final_logs_local_path, self.s3_bucket_name, final_logs_s3_path)

        logger.info("S3 upload logs finished")

    def clean(self):
        logger.info("Starting removing generated files")
        for directory in [sra_dir, fastq_dir, salmon_dir, deseq2_dir]:
            clean_dir(directory)
        logger.info("Finished removing generated files")

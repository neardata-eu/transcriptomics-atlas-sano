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
            fasterq_dump, self.srr_id
        )

        self.make_timestamps(
            salmon, self.srr_id, self.metadata
        )

        self.make_timestamps(
            deseq2_salmon, self.srr_id
        )

        self.upload_normalized_counts_to_s3()

    def upload_normalized_counts_to_s3(self):
        logger.info("S3 upload starting")
        bucket = self.s3_bucket_name if self.metadata["salmon_mapping_rate [%]"] >= 30 else self.s3_bucket_name_low_mr
        self.s3.meta.client.upload_file(f'{deseq2_dir}/{self.srr_id}_normalized_counts.txt', bucket,
                                        f"{self.tissue_name}/{self.srr_id}_normalized_counts.txt")
        self.metadata["bucket"] = bucket
        logger.info("S3 upload finished")

    def clean(self):
        logger.info("Starting removing generated files")
        for directory in [sra_dir, fastq_dir, salmon_dir, deseq2_dir]:
            clean_dir(directory)
        logger.info("Finished removing generated files")

import pytest
from moto import mock_aws

from pipeline_steps import prefetch, fasterq_dump, star, deseq2_star
from test_pipeline import TestPipeline


@mock_aws
class TestSTARPipeline(TestPipeline):
    tissue_name = "endothelium"
    star_srr_id = "SRR8823306"

    @pytest.mark.essential
    def test_pipeline(self):
        self.run_pipeline(self.tissue_name, self.star_srr_id)

        ## CHECK S3 AND DYNAMODB
        s3_base_path = f"STAR/low_mapping_rate/{self.tissue_name}"
        s3_path_row_counts = f"{s3_base_path}/row_counts/{self.star_srr_id}_STAR_row_counts.csv"
        s3_path_normalized_counts = f"{s3_base_path}/normalized_counts/{self.star_srr_id}_STAR_normalized_counts.tsv"
        self.bucket.Object(s3_path_row_counts).load()
        self.bucket.Object(s3_path_normalized_counts).load()

        assert "Item" in self.table.get_item(Key={"SRR_id": self.star_srr_id})
        print(self.table.get_item(Key={"SRR_id": self.star_srr_id}))

    def test_early_stopping(self):
        srr_id = "SRR16541678"
        self.run_pipeline("dummy_name", srr_id)

        assert self.table.get_item(Key={"SRR_id": srr_id})["Item"]["error_type"] == "Early stopping"

    def test_star(self):
        prefetch(self.star_srr_id)
        fasterq_dump(self.star_srr_id)
        star(self.star_srr_id, metadata={})

    def test_deseq2_star(self):
        prefetch(self.star_srr_id)
        fasterq_dump(self.star_srr_id)
        star(self.star_srr_id, metadata={})
        deseq2_star(self.star_srr_id)

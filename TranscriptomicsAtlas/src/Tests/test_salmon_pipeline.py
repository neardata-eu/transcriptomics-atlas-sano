import pytest
from moto import mock_aws

from pipeline_steps import prefetch, fasterq_dump, salmon, deseq2_salmon
from test_pipeline import TestPipeline


@mock_aws
class TestSalmonPipeline(TestPipeline):
    @pytest.mark.essential
    def test_salmon_pipeline(self):
        self.run_pipeline(self.tissue_name, self.srr_id)

        ## CHECK S3 AND DYNAMODB
        s3_base_path = f"Salmon/low_mapping_rate/{self.tissue_name}"
        s3_path_row_counts = f"{s3_base_path}/row_counts/{self.srr_id}_salmon_row_counts.csv"
        s3_path_normalized_counts = f"{s3_base_path}/normalized_counts/{self.srr_id}_salmon_normalized_counts.tsv"
        self.bucket.Object(s3_path_row_counts).load()
        self.bucket.Object(s3_path_normalized_counts).load()

        assert "Item" in self.table.get_item(Key={"SRR_id": self.srr_id})
        print(self.table.get_item(Key={"SRR_id": self.srr_id}))

    def test_salmon(self):
        prefetch(self.srr_id)
        fasterq_dump(self.srr_id)
        salmon(self.srr_id, metadata={})

    def test_deseq2_salmon(self):
        prefetch(self.srr_id)
        fasterq_dump(self.srr_id)
        salmon(self.srr_id, metadata={})
        deseq2_salmon(self.srr_id)

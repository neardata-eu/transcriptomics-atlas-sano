import os

import pytest
from moto import mock_aws

from consumer import start_pipeline
from utils import PipelineError, clean_dir
from config import sra_dir, fastq_dir, salmon_dir, deseq2_dir
from pipeline_steps import prefetch, fasterq_dump, salmon, deseq2_salmon
from test_setup import BaseCase


@mock_aws
class TestPipeline(BaseCase):
    tissue_name = "kidney_cells"
    srr_id = "SRR13210228"  # 84 kB, single fastq

    def run_pipeline(self, tissue_name, srr_id):
        entries = [{"Id": srr_id, "MessageBody": f"{tissue_name}-{srr_id}"}]
        self.queue.send_messages(Entries=entries)

        start_pipeline(mode="job")

    def test_prefetch_big_sra_file(self):
        srr_id = "SRR13179686"  # 37 GB in size

        with pytest.raises(PipelineError):
            prefetch(srr_id)

    def test_prefetch(self):
        prefetch(self.srr_id)

        assert os.path.exists(f"{sra_dir}/{self.srr_id}.sra")

    def test_fasterq_dump(self):
        prefetch(self.srr_id)
        fasterq_dump(self.srr_id)

        assert os.path.exists(f"{fastq_dir}/{self.srr_id}.fastq")

    def test_skipping_processed_sra_ids(self):
        item = {"SRR_id": self.srr_id}
        entries = [{"Id": self.srr_id, "MessageBody": f"{self.tissue_name}-{self.srr_id}"}]
        self.table.put_item(Item=item)
        self.queue.send_messages(Entries=entries)

        start_pipeline(mode="job")

        assert item == (self.table.get_item(Key={"SRR_id": self.srr_id}))["Item"]

    def test_clean_dirs(self):
        self.run_pipeline(self.tissue_name, self.srr_id)

        for directory in [sra_dir, fastq_dir, salmon_dir, deseq2_dir]:
            assert not os.listdir(directory)

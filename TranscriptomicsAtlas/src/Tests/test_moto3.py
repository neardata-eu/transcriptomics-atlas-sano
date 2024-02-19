from moto import mock_aws

from test_setup import BaseCase


@mock_aws
class TestPipeline(BaseCase):
    def test_sqs(self):
        messages = ["kidney_cells-SRR13210228"]
        entries = [{"Id": srr_id, "MessageBody": srr_id} for srr_id in messages]
        self.queue.send_messages(Entries=entries)

        msg_back = self.queue.receive_messages(MaxNumberOfMessages=1, WaitTimeSeconds=5)[0]
        srr_id = msg_back.body

        assert messages[0] == srr_id

    def test_s3(self):
        with open("test_normalized_counts.tsv", "w+") as f:
            f.write("test")
        self.salmon_bucket.Object(f"test.txt").upload_file('test_normalized_counts.tsv')
        self.salmon_bucket.Object(f"test.txt").load()

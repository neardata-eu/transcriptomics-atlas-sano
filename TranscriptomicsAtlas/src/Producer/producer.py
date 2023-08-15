import boto3
from tqdm import trange

sqs = boto3.resource("sqs")
queue = sqs.get_queue_by_name(QueueName="NearData_queue_container")

with open("../../data/SRA_IDs/random_99_small_SRA_IDs.txt", "r") as f:
    sra_ids_all = [sra_id.strip() for sra_id in f.readlines()]

for i in trange(0, len(sra_ids_all), 10):
    sra_ids = sra_ids_all[i:i + 10]
    entries = [{"Id": sra_id, "MessageBody": sra_id} for sra_id in sra_ids]
    queue.send_messages(Entries=entries)
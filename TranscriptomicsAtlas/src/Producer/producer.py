import boto3
import pandas as pd
from tqdm import trange

sqs = boto3.resource("sqs")
queue = sqs.get_queue_by_name(QueueName="Salmon_queue")

df = pd.read_csv("3k_input_df.csv", index_col=0)

messages = list(map(lambda x: "-".join(x), zip(df["tissue_name"], df["SRR_id"])))
print(len(list(messages)))

for i in trange(0, len(messages), 10):
    srr_ids = messages[i:i + 10]
    entries = [{"Id": srr_id, "MessageBody": srr_id} for srr_id in srr_ids]
    queue.send_messages(Entries=entries)

import os

import boto3
import pandas as pd
from tqdm import trange

sqs = boto3.resource("sqs")
queue = sqs.get_queue_by_name(QueueName="NearData_queue")


def get_only_vaild_srr(tissue_name):
    tissue_srr_df = pd.read_csv(f"../../data/Tissues/runs/RunInfo/{tissue_name}.csv")
    no_tumor_df = tissue_srr_df[tissue_srr_df['Tumor'] == 'no']
    human_only_df = no_tumor_df[no_tumor_df["ScientificName"] == "Homo sapiens"]
    public_only_df = human_only_df[human_only_df["Consent"] == "public"]
    valid_srr_df = public_only_df

    return valid_srr_df


def remove_previously_sent_srr(tissues_df, tissue_name):
    srr_ids_filepath = f"../../data/Tissues/runs/inputs/{tissue_name}_ids.csv"
    if os.path.exists(srr_ids_filepath):
        previous_srr = pd.read_csv(srr_ids_filepath)["Run"]
        tissues_df = tissues_df[~tissues_df['Run'].isin(previous_srr)]
    return tissues_df


def create_or_append_input_csv(srr_ids, tissue_name):
    srr_ids_filepath = f"../../data/Tissues/runs/inputs/{tissue_name}_ids.csv"
    if not os.path.exists(srr_ids_filepath):
        srr_ids.to_csv(srr_ids_filepath)
    else:
        previous_srr = pd.read_csv(srr_ids_filepath)["Run"]
        pd.concat([previous_srr, srr_ids]).reset_index(drop=True).to_csv(srr_ids_filepath)


def sample_n_or_take_all(tissues_df, n):
    if len(tissues_df) < n:
        return tissues_df["Run"]
    return tissues_df.sample(n=n, random_state=42)["Run"].reset_index(drop=True)


def get_previous_srr_ids(tissue_name):
    srr_ids_filepath = f"../../data/Tissues/runs/inputs/{tissue_name}_ids.csv"
    previous_srr = pd.read_csv(srr_ids_filepath)["Run"]
    return previous_srr


tissue_names = ["adipose tissue", "breast cells", "endometrium", "endothelium", "epithelium", "fibroblasts",
                "heart muscle", "intestine", "kidney cells", "liver tissues", "lymphocytes", "lymphoid tissue",
                "nervous cells", "ovarian cells", "prostate tissue", "retina", "smooth muscle",
                "thyroid cells", "urinary bladder"]  # , "neutrophiles" , "fibrocytes"

for tissue_name in tissue_names[11:12]:
    print(tissue_name)
    tissues_df = get_only_vaild_srr(tissue_name)
    tissue_name = tissue_name.replace(' ', '_')
    tissues_df = remove_previously_sent_srr(tissues_df, tissue_name)
    srr_ids = sample_n_or_take_all(tissues_df, 500)
    # srr_ids = get_previous_srr_ids(tissue_name)
    create_or_append_input_csv(srr_ids, tissue_name)

    messages = [f"{tissue_name}-{srr_id}" for srr_id in srr_ids]
    print(f"N_messages: {len(messages)}")

    for i in trange(0, len(messages), 10):
        srr_ids = messages[i:i + 10]
        entries = [{"Id": srr_id, "MessageBody": srr_id} for srr_id in srr_ids]
        queue.send_messages(Entries=entries)

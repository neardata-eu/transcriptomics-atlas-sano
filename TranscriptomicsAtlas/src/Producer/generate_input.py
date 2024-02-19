import pandas as pd
from tqdm import tqdm


def get_only_valid_srr(tissue_name):
    tissue_srr_df = pd.read_csv(f"../../data/Tissues/runs/RunInfo/{tissue_name}.csv")
    no_tumor_df = tissue_srr_df[tissue_srr_df['Tumor'] == 'no']
    human_only_df = no_tumor_df[no_tumor_df["ScientificName"] == "Homo sapiens"]
    public_only_df = human_only_df[human_only_df["Consent"] == "public"]
    valid_srr_df = public_only_df

    return valid_srr_df


def sample_n_or_take_all(tissues_df, n):
    if len(tissues_df) < n:
        return tissues_df
    return tissues_df.sample(n=n, random_state=42).reset_index(drop=True)


def filter_srr_ids(tissues_df):
    invalid_ids_df = pd.read_csv("../../analysis/Salmon_metadata/invalid_ids.csv")
    invalid_ids = set(invalid_ids_df["SRR_id"])
    tissues_df = tissues_df[~tissues_df["Run"].isin(invalid_ids)]
    return tissues_df


tissue_names = ["adipose tissue", "breast cells", "endometrium", "endothelium", "epithelium", "fibroblasts",
                "heart muscle", "intestine", "kidney cells", "liver tissues", "lymphocytes", "lymphoid tissue",
                "nervous cells", "ovarian cells", "prostate tissue", "retina", "smooth muscle",
                "thyroid cells", "urinary bladder"]  # , "neutrophiles" , "fibrocytes"

inputs = []
for tissue_name in tqdm(tissue_names):
    tissues_df = get_only_valid_srr(tissue_name)
    tissues_df = filter_srr_ids(tissues_df)
    sample_df = sample_n_or_take_all(tissues_df, 500)
    sample_df["tissue_name"] = tissue_name.replace(' ', '_')
    inputs.append(sample_df)

input_df = pd.concat(inputs).reset_index(drop=True)
input_df = input_df.rename(columns={"Run": "SRR_id"})
input_df.to_csv("full_input_df.csv")

import os
import boto3
import pandas as pd
from tqdm import tqdm

cw_client = boto3.client("cloudwatch")
stat_abbrev_map = {"Average": "Avg", "None": "", "Maximum": "Max", "Sum": "Sum", "Count": "n"}
unit_abbrev_map = {'[Percent]': '[%]', '[Milliseconds]': '[ms]', '[Count]': '[n]', '[None]': '[]'}

with open("metric_names.txt", "r") as f:
    metric_names, statistics, units = zip(*(line.strip().split(',') for line in f))


def get_all_metrics_for_instance(namespace, instance_id, start_time, end_time):
    queries = []
    for metric_name, statistic in zip(metric_names, statistics):
        query = {
            'Id': metric_name,
            'MetricStat': {
                'Metric': {
                    'Namespace': namespace,
                    'MetricName': metric_name,
                    'Dimensions': [
                        {
                            'Name': 'ContainerId',
                            'Value': instance_id
                        }
                    ]
                },
                'Period': 10,
                'Stat': statistic
            }
        }
        queries.append(query)

    response = cw_client.get_metric_data(MetricDataQueries=queries, StartTime=start_time, EndTime=end_time)

    metrics_dfs = []
    for i, metrics in enumerate(response["MetricDataResults"]):
        timestamps = pd.Series(metrics["Timestamps"], name="Timestamp")
        values = pd.Series(metrics["Values"], name=f"{metric_names[i]} [{stat_abbrev_map[statistics[i]]}] [{units[i]}]")
        metrics_df = pd.concat([timestamps, values], axis=1)
        metrics_dfs.append(metrics_df)

    merged = metrics_dfs[0]
    for metrics_df in metrics_dfs[1:]:
        merged = pd.merge(merged, metrics_df, on="Timestamp", how="outer")

    for unit, abbrev in unit_abbrev_map.items():
        merged = merged.rename(columns=lambda x: x.replace(unit, abbrev))
    procstat_columns = sorted([col for col in merged.columns if col.startswith('procstat')])
    other_columns = sorted([col for col in merged.columns if not col.startswith('procstat')])
    sorted_columns = other_columns + procstat_columns

    return merged[sorted_columns].sort_values("Timestamp").reset_index(drop=True)


namespace = "Containers/Development/Process"
start_time = "2023-08-14T16:36:00"
end_time = "2023-08-14T19:36:00"
# instance_ids = ["i-0f94d08d1318d61a5", "i-0bfdeba94d645b3fa", "i-07c2da38a3dd06322", "i-0ec771083b7f36473",
#                 "i-0ca0647f2c49fccdb", "i-076094e027186f6bd", "i-0516c994fa6a5973a", "i-0a490a6b0d4dec87c"]
container_ids = ["4501679/1", "4501679/2", "4501679/3", "4501679/4",
                 "4501679/5", "4501679/6", "4501679/7", "4501679/8"]

datadir = "metric_data/" + start_time.split("T")[0] + "-hpc"
os.makedirs(datadir, exist_ok=True)
for instance_id in tqdm(container_ids):
    metric_df = get_all_metrics_for_instance(namespace, instance_id, start_time, end_time)
    metric_df.to_csv(f"{datadir}/{instance_id.replace('/', '_')}.csv")

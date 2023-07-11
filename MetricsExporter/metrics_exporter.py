import os
import json
import asyncio
import pandas as pd
from tqdm import tqdm

with open("metric_names.txt", "r") as f:
    # metric_names, statistics = [line.strip() for line in f.readlines()]
    metric_names, statistics = zip(*(line.strip().split(',') for line in f))

async def get_all_metrics_for_instance(namespace, instance_id, start_time, end_time):
    async def get_single_metric(metric_name, statistic):
        cmd = f"""aws cloudwatch get-metric-statistics \
                    --namespace {namespace} --metric-name {metric_name} \
                    --dimensions Name=InstanceId,Value={instance_id} \
                    --start-time {start_time} --end-time {end_time} \
                    --period 10 --statistics {statistic} \
                    --output json --region us-east-1"""
        process = await asyncio.create_subprocess_exec(*cmd.split(), stdout=asyncio.subprocess.PIPE)
        stdout, stderr = await process.communicate()

        return json.loads(stdout.decode().strip())

    tasks = []
    for metric_name, statistic in zip(metric_names, statistics):
        task = asyncio.ensure_future(get_single_metric(metric_name, statistic))
        tasks.append(task)

    task_results = []
    with tqdm(total=len(tasks)) as pbar:
        for task in asyncio.as_completed(tasks):
            result = await task
            task_results.append(result)
            pbar.update(1)

    metrics_dfs = []
    for resp in task_results:
        if len(resp["Datapoints"]) == 0:
            continue
        df = pd.DataFrame.from_dict(resp["Datapoints"])
        if "Unit" in df:
            metric_unit = df["Unit"][0]
            df = df.rename({"Average": f"{resp['Label']} [Avg] [{metric_unit}]"}, axis=1)
            df = df.rename({"Sum": f"{resp['Label']} [Sum] [{metric_unit}]"}, axis=1)
            df = df.rename({"Maximum": f"{resp['Label']} [Max] [{metric_unit}]"}, axis=1)
            df = df.rename(columns=lambda x: x.replace('[Percent]', '[%]').replace('[Milliseconds]', '[ms]').replace('[Count]','[n]').replace('[None]', '[]'))

            df = df.drop("Unit", axis=1)
        else:
            print(resp)
        df = df.sort_values("Timestamp").reset_index(drop=True)

        metrics_dfs.append(df)

    if len(metrics_dfs) == 0:
        return
    merged = metrics_dfs[0]
    for metric_df in metrics_dfs[1:]:
        merged = pd.merge(merged, metric_df, on="Timestamp", how="outer")
    merged = merged.reset_index(drop=True)

    procstat_columns = sorted([col for col in merged.columns if col.startswith('procstat')])
    other_columns = sorted([col for col in merged.columns if not col.startswith('procstat')])
    sorted_columns = other_columns + procstat_columns
    return merged[sorted_columns].sort_values("Timestamp").reset_index(drop=True)


def fetch_all(namespace, instance_id, start_time, end_time):
    return asyncio.run(get_all_metrics_for_instance(namespace, instance_id, start_time, end_time))


namespace = "EC2Instances/Development"
start_time = "2023-07-05T10:30:00"
end_time = "2023-07-05T13:30:00"
instance_ids = ["i-0f94d08d1318d61a5", "i-0bfdeba94d645b3fa", "i-07c2da38a3dd06322", "i-0ec771083b7f36473",
                "i-0ca0647f2c49fccdb", "i-076094e027186f6bd", "i-0516c994fa6a5973a", "i-0a490a6b0d4dec87c"]

os.makedirs("data"+start_time.split("T")[0], exist_ok=True)
for instance_id in instance_ids:
    metric_df = fetch_all(namespace, instance_id, start_time, end_time)
    metric_df.to_csv(f"data/2023-07-05/{instance_id}.csv")
    print(metric_df)

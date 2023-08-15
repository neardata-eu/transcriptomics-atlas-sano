import os
import pandas as pd


def merge_csv_files(directory1, directory2, output_directory):
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    for filename in os.listdir(directory1):
        if filename.endswith('.csv'):
            file_path1 = os.path.join(directory1, filename)
            file_path2 = os.path.join(directory2, filename)
            output_path = os.path.join(output_directory, filename)

            if os.path.exists(file_path2):
                df1 = pd.read_csv(file_path1, index_col=0).dropna(axis=1, how='all')
                df2 = pd.read_csv(file_path2, index_col=0).dropna(axis=1, how='all')

                merged_df = pd.concat([df1, df2]).drop_duplicates()
                merged_df.sort_values(by='Timestamp', inplace=True)
                merged_df.to_csv(output_path)


if __name__ == "__main__":
    dir1 = "data/2023-08-12-hpc-part1"
    dir2 = "data/2023-08-12-hpc-part2"
    output_dir = "metric_data/2023-08-12-hpc"
    merge_csv_files(dir1, dir2, output_dir)

import os
import subprocess

nproc = subprocess.run(["nproc"], capture_output=True, text=True).stdout.strip()
my_env = {**os.environ, 'PATH': '/opt/TAtlas/sratoolkit.3.0.1-ubuntu64/bin:'
                                '/opt/TAtlas/salmon-latest_linux_x86_64/bin:' + os.environ['PATH']}
work_dir = "/home/ubuntu/TAtlas"
sra_dir = f"{work_dir}/sratoolkit/sra"
fastq_dir = f"{work_dir}/fastq"
salmon_dir = f"{work_dir}/salmon"
deseq2_dir = f"{work_dir}/R_output"
metadata_dir = f"{work_dir}/metadata"

for directory in [sra_dir, fastq_dir, salmon_dir, deseq2_dir, metadata_dir]:
    os.makedirs(directory, exist_ok=True)

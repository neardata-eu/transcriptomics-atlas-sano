import os

nproc = str(len(os.sched_getaffinity(0)))
my_env = {**os.environ, 'PATH': '/opt/TAtlas/sratoolkit.3.0.1-ubuntu64/bin:'
                                '/opt/TAtlas/salmon-latest_linux_x86_64/bin:'
                                '/opt/TAtlas/STAR-2.7.10b/bin/Linux_x86_64:' + os.environ['PATH']}
index_release = os.environ.get("index_release", "")
work_dir = "/home/ubuntu/TAtlas"
sra_dir = f"{work_dir}/sratoolkit/sra"
fastq_dir = f"{work_dir}/fastq"
salmon_dir = f"{work_dir}/salmon"
salmon_index_dir = "/opt/TAtlas/salmon_index_release111/"
deseq2_dir = f"{work_dir}/R_output"
metadata_dir = f"{work_dir}/metadata"
star_dir = f"{work_dir}/STAR"
star_data_dir = "/opt/TAtlas/STAR_data"
star_index_dir = f"/opt/TAtlas/STAR_data/STAR_index/STAR_index_hg38_gtf_release_{index_release}/"

for directory in [sra_dir, fastq_dir, salmon_dir, deseq2_dir, metadata_dir, star_dir]:
    os.makedirs(directory, exist_ok=True)

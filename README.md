# Transcriptomics Atlas Pipeline: Cloud vs HPC - Reproducibility Guide:

1. Create a single EC2 instance on AWS (or use my AMI: `ami-0ebb995fac9a140ef` and skip to point 5):
    * Type: Ubuntu Server 22.04, m6a.large, 100GB EBS (GP3 type, 250MiB/s throughput, 3000IOPS)
    * Upload `EC2/ec2_cwagent_config.json` to SSM Parameter Store as an advanced parameter named `ec2_cwagent_config`. 
    * Copy and install `ec2_install.sh` from `./TranscriptomicsAtlas/EC2`
    * Copy `data/.ncbi` to `/home/ubuntu/.ncbi`
2. Prepare source code
    * Upload `src/Consumer` code to the instance. 
    * Upload `src/scripts/count_normalization.R` to `/opt/TAtlas/DESeq2/count_normalization.R`
    * Upload `data/DESeq2/tx2gene.gencode.v42.csv` to `/opt/TAtlas/DESeq2/tx2gene.gencode.v42.csv`
3. Generate Salmon index:
    * Download using wget: `https://ftp.ensembl.org/pub/release-109/fasta/homo_sapiens/cdna/Homo_sapiens.GRCh38.cdna.all.fa.gz`
    * Unpack and run `salmon index -t Homo_sapiens.GRCh38.cdna.all.fa -i /opt/TAtlas/salmon_index`
4. Create AMI from the instance 
5. Set up infrastructure:
   * Install Terraform
   * Update `main.tf` in `./TranscriptomicsAtlas/Terraform`
      - Update image_id in launch_template with your newly created
      - Create 4 new buckets in S3 and replace them in `main.tf`
      - Create IAM instance profile with access permissions to CloudWatch and S3, update the script
      - If you want to SSH to any instance - update security group with your IP address and generate new access key (replace "vockey" in launch template)
   * Run `terraform apply` in `./TranscriptomicsAtlas/Terraform`
6. Prepare and run EC2 experiments:
    * Update `./MetricsExporter/metrics_exporter.py` with current time and instance-ids of your 8 running instances.
      * The end_time in this script should be 3 hours from now. Since CloudWatch metrics are retained only for 3 hours for sub-minute granularity you may need to run `metrics_exporter.py` twice (with new start_time and end_time) if the simulation does not finish within 3 hours. Beware: the script overwrites files in the same directory thus update paths for 2nd execution to prevent overwrite, then merge first 3 hours of metrics and the rest. # TODO simplify 
    * Verify queue name in `./TranscriptomicsAtlas/src/Producer/producer.py`
    * Send the SRR_IDs by running `producer.py`
    * After 3 hours or when SQS queue is empty run `metrics_exporter.py` to gather metrics.
    * Turn off EC2 instances.
    * Download metadata from the S3 bucket you created to `Metrics_exporter/metadata/{current_date}`.
    * Update paths to your data in `MetricsExporter/performance_analysis.ipynb` and run it.
7. Prepare and run HPC experiments:
   * Have a Docker installed and a DockerHub account. Connect/Log-in to DockerHub using Docker.
   * Create a repository on DockerHub, update path to your repository in `TranscriptomicsAtlas/Makefile`
   * Run `make all` in `TranscriptomicsAtlas` directory
   * Reserve a node on your HPC only for your experiment. You need 8 jobs: each requires 2CPU and 8GB RAM. 
   * Regarding the HPC environment you work in the next steps may be different. I assume `Ares` cluster in Cyfronet which uses apptainer as a containerization software.
     * Log in to Apptainer
     * Use `apptainer pull docker://docker.io/{account_name}/{repo_name}:{tag}`
     * Copy `TranscriptomicsAtlas/HPC/salmon_pipeline.slurm` to your home dir on HPC. Update args and command for your use case.
     * Copy AWS credentials for a role that has both CloudWatch and S3 access. Paste it in your home dir on HPC under .aws dir. Update sbatch script with this path.
       * You need to paste credentials twice: Once with \[default\] tag and below with \[AmazonCloudWatchAgent\] tag.
     * Copy `/TranscriptomicsAtlas/data/.ncbi` to your home dir on HPC. Update sbatch script with this path.
     * Update sbatch script with path to your .sif image.
     * Schedule 8 jobs on your reserved node using the slurm script. Wait for the running state.
     * Send the SRR_IDs by running `producer.py`
     * Once again after 3 hours or when SQS queue is empty run `metrics_exporter.py` to gather metrics.
   * Download metadata from the S3 bucket you created to `Metrics_exporter/metadata{current_date}`.
   * Update paths to your data in `MetricsExporter/performance analysis.ipynb` and run it.
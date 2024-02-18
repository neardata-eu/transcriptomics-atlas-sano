#!/bin/env bash
#SBATCH -J salmon_container
#SBATCH -N 1
#SBATCH --ntasks-per-node=2
#SBATCH --mem-per-cpu=8GB
#SBATCH --time=20:00:00
#SBATCH -A plgsano4-cpu
#SBATCH --array=1-200
#SBATCH -p plgrid
#SBATCH --output="output3/output-%A_%a.out"
#SBATCH --error="output3/error-%A_%a.err"


apptainer run --home /home/ubuntu --compat \
              --mount type=bind,source=/net/people/plgrid/plgpkica/.aws/,destination=/home/ubuntu/.aws/ \
              --mount type=bind,source=/net/people/plgrid/plgpkica/.ncbi/,destination=/home/ubuntu/.ncbi/ \
              --mount type=bind,source=$TMPDIR,destination=/home/ubuntu/TAtlas \
              --mount type=bind,source=$TMPDIR,destination=/opt/aws/amazon-cloudwatch-agent/etc/ \
              --env AWS_SHARED_CREDENTIALS_FILE=/home/ubuntu/.aws/credentials \
              --env SLURM_JOB_ID=$SLURM_JOB_ID \
              --env SLURM_ARRAY_TASK_ID=SLURM_ARRAY_TASK_ID \
              --env HOSTNAME=$SLURMD_NODENAME \
              --env execution_mode="HPC_container" \
              --env queue_name="Salmon_queue_hpc" \
              --env dynamodb_metadata_table="neardata-tissues-salmon-metadata_hpc" \
              --env s3_bucket_name="transcriptomics-atlas" \
              --env index_release="111" \
              /net/ascratch/people/plgpkica/neardata/salmonpipeline_v1-3.sif


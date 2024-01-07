#!/bin/env bash
#SBATCH -J salmon_experiment
#SBATCH -N 1
#SBATCH --ntasks=48
#SBATCH --mem=80GB
#SBATCH --time=08:00:00
#SBATCH -A plgsano4-cpu
#SBATCH -p plgrid-now
#SBATCH --output="output/output-%A_%a.out"
#SBATCH --error="output/error-%A_%a.err"

# sbatch salmon_plgnow.sbatch

for value in {1..8}; do
    mkdir "$SCRATCHDIR/$value"
    cmd="apptainer run --home /home/ubuntu --compat \
              --mount type=bind,source=/net/people/plgrid/plgpkica/.aws/,destination=/home/ubuntu/.aws/ \
              --mount type=bind,source=/net/people/plgrid/plgpkica/.ncbi/,destination=/home/ubuntu/.ncbi/ \
              --mount type=bind,source=$SCRATCHDIR/$value,destination=/home/ubuntu/TAtlas \
              --mount type=bind,source=$SCRATCHDIR/$value,destination=/opt/aws/amazon-cloudwatch-agent/etc/ \
              --env AWS_SHARED_CREDENTIALS_FILE=/home/ubuntu/.aws/credentials \
              --env SLURM_JOB_ID=$SLURM_JOB_ID\_$value \
              /net/ascratch/people/plgpkica/neardata/salmonpipeline_backoff.sif"
    srun -N1 -n1 --cpus-per-task=2 --mem-per-cpu=4GB --time=08:00:00 $cmd &  # dont put " around $cmd or it will break
done

wait
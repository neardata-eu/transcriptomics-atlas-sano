#!/bin/env bash
## Nazwa zlecenia
#SBATCH -J salmon_experiment
## Liczba alokowanych węzłów
#SBATCH -N 1
## Liczba zadań per węzeł (domyślnie jest to liczba alokowanych rdzeni na węźle)
#SBATCH --ntasks=48
## Ilość pamięci
#SBATCH --mem=80GB
## Maksymalny czas trwania zlecenia (format DD-HH:MM:SS)
#SBATCH --time=08:00:00
## Nazwa grantu do rozliczenia zużycia zasobów
#SBATCH -A plgsano4-cpu
## Specyfikacja partycji
#SBATCH -p plgrid-now
## Plik ze standardowym wyjściem
#SBATCH --output="output/output-%A_%a.out"
## Plik ze standardowym wyjściem błędów
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
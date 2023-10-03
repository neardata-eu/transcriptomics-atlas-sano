#!/bin/env bash
## Nazwa zlecenia
#SBATCH -J salmon_container
## Liczba alokowanych węzłów
#SBATCH -N 1
## Liczba zadań per węzeł (domyślnie jest to liczba alokowanych rdzeni na węźle)
#SBATCH --ntasks-per-node=4
## Ilość pamięci przypadającej na jeden rdzeń obliczeniowy (domyślnie 4GB na rdzeń)
#SBATCH --mem-per-cpu=4GB
## Maksymalny czas trwania zlecenia (format DD-HH:MM:SS)
#SBATCH --time=03:00:00
## Nazwa grantu do rozliczenia zużycia zasobów
#SBATCH -A plgsano4-cpu
## Specyfikacja partycji
#SBATCH -p plgrid
## Plik ze standardowym wyjściem
#SBATCH --output="output-%A_%a.out"
## Plik ze standardowym wyjściem błędów
#SBATCH --error="error-%A_%a.err"

apptainer run --home /home/ubuntu --compat \
              --mount type=bind,source=/net/people/plgrid/plgpkica/.aws/,destination=/home/ubuntu/.aws/ \
              --mount type=bind,source=/net/people/plgrid/plgpkica/.ncbi/,destination=/home/ubuntu/.ncbi/ \
              --mount type=bind,source=$TMPDIR,destination=/home/ubuntu/TAtlas \
              --mount type=bind,source=$TMPDIR,destination=/opt/aws/amazon-cloudwatch-agent/etc/ \
              --env AWS_SHARED_CREDENTIALS_FILE=/home/ubuntu/.aws/credentials \
              --env SLURM_JOB_ID=$SLURM_JOB_ID \
              /net/ascratch/people/plgpkica/neardata/salmonpipeline_backoff.sif bash



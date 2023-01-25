#!/bin/bash -l
## nazwa
#SBATCH -J star_mapping
## Liczba alokowanych wezlow
#SBATCH -N 1
## Liczba zadan per wezel
#SBATCH --ntasks-per-node=12
## ilosc pamieci
#SBATCH --mem=80GB
## Maksymalny czas trwania zlecenia (format HH:MM:SS)
#SBATCH --time=01:00:00
## nazwa grantu
#SBATCH -A plggenomis-cpu
## partycja
#SBATCH -p plgrid-testing
## plik standardowe wyjscie
#SBATCH --output=SRR8206145_normal_output.out
## plik wyjscie bledu
#SBATCH --error=SRR8206145_normal_error.err
## typ wiadomosci
#SBATCH --mail-type ALL
##adres
#SBATCH --mail-user sabina.licholai@gmail.com



module load sra-toolkit/3.0.0-centos_linux64
i=$1

cd $SLURM_SUBMIT_DIR
srun /bin/hostname


fastq-dump --split-files  -v "$i"
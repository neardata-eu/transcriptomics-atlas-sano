#!/bin/bash -l
## nazwa
#SBATCH -J salmon_skrypt_short
## Liczba alokowanych wezlow
#SBATCH -N 1
## Liczba zadan per wezel 
#SBATCH --ntasks-per-node=12
## ilosc pamieci
#SBATCH --mem=120GB
## Maksymalny czas trwania zlecenia (format HH:MM:SS)
#SBATCH --time=01:00:00 
## nazwa grantu
#SBATCH -A plggenomis-cpu
## partycja
#SBATCH -p plgrid
## plik standardowe wyjscie
#SBATCH --output="salmon_skrypt.out"
## plik wyjscie bledu
#SBATCH --error="salmon_skrypt.err"
## typ wiadomosci
#SBATCH --mail-type ALL
##adres
#SBATCH --mail-user sabina.licholai@gmail.com


module load salmon/1.5.2-gompi-2021b

cd $SLURM_SUBMIT_DIR

srun /bin/hostname

salmon index -t human_transcriptome.fa -i human_transcriptome_index

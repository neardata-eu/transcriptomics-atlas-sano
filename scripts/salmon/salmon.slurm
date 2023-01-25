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


i="$1"

salmon quant -p 12 --useVBOpt -i human_transcriptome_index -l A -1 "$i".1.fastq.gz -2 "$i".2.fastq.gz   -o quant_gene_salmon_108/"$i"

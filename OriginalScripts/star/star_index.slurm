#!/bin/bash -l
## nazwa
#SBATCH -J star_mapping
## Liczba alokowanych wezlow
#SBATCH -N 1
## Liczba zadan per wezel
#SBATCH --ntasks-per-node=12
## ilosc pamieci
#SBATCH --mem=180GB
## Maksymalny czas trwania zlecenia (format HH:MM:SS)
#SBATCH --time=12:00:00
## nazwa grantu
#SBATCH -A plggenomis-cpu
## partycja
#SBATCH -p plgrid
## plik standardowe wyjscie
#SBATCH --output=SRR8206145_normal_output.out
## plik wyjscie bledu
#SBATCH --error=SRR8206145_normal_error.err
## typ wiadomosci
#SBATCH --mail-type ALL
##adres
#SBATCH --mail-user sabina.licholai@gmail.com


module load star/2.7.8a-gcc-10.3.0

cd $SLURM_SUBMIT_DIR
srun /bin/hostname


DIR_DATA="/net/ascratch/people/plglicholai/sl/STAR/raw_sequences"
INDEX="/net/ascratch/people/plglicholai/sl/STAR/index_hg38"
REF="/net/ascratch/people/plglicholai/sl/reference"
#UMI="/net/scratch/people/plglicholai/sl/single/3M-february-2018.txt.gz"

STAR --runThreadN 8 --runMode genomeGenerate --genomeDir "$INDEX" --genomeFastaFiles "$REF"/Homo_sapiens.GRCh38.dna.toplevel.fa --limitGenomeGenerateRAM 168632691637 


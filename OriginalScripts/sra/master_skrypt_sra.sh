for i in SRR13696760 SRR13696761 SRR13696762 SRR13696763; do


	echo "$i" 
	mkdir -p logs/"$i"
	sbatch -o logs/$i/output_sra.out -e logs/$i/error_sra.er -J sra_gzip_"$i" sra.slurm "$i"


done





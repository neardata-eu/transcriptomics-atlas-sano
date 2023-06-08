for i in SRR11858779; do


	echo "$i" 
	mkdir -p logs/"$i"
	sbatch -o logs/$i/output_star.out -e logs/$i/error_star.er -J star_"$i" star.slurm "$i"


done





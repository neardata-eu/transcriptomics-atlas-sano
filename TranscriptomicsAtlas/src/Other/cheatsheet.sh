SRA_ID="SRR11982817"
work_dir="/home/ubuntu/TAtlas"
fastq_dir="$work_dir/fastq"
star_dir="$work_dir/STAR"

# prefetch:
prefetch $SRA_ID --progress

# fasterq-dump:
fasterq-dump $SRA_ID -f --threads $(nproc) --outdir $fastq_dir --progress

# salmon with single fastq:
salmon quant --threads $(nproc) --useVBOpt -i /opt/TAtlas/salmon_index_release111/ -l A -o $work_dir/salmon/$SRA_ID -r $fastq_dir/$SRA_ID.fastq
# salmon with double fastq:
salmon quant --threads $(nproc) --useVBOpt -i /opt/TAtlas/salmon_index_release111/ -l A -o $work_dir/salmon/$SRA_ID -1 $fastq_dir/"$SRA_ID"_1.fastq -2 $fastq_dir/"$SRA_ID"_2.fastq

# DESeq2_salmon
Rscript /opt/TAtlas/DESeq2/Salmon_count_normalization.R $SRA_ID

#STAR  with single fastq
STAR --genomeDir /opt/TAtlas/STAR_data/STAR_index/STAR_index_hg38_gtf_release_111/ \
	 --genomeLoad LoadAndKeep --runThreadN $(nproc) \
	 --outFileNamePrefix $star_dir/$SRA_ID/ \
	 --outSAMtype BAM SortedByCoordinate \
	 --outSAMunmapped Within \
	 --quantMode GeneCounts \
	 --limitBAMsortRAM 30064771072 \
	 --outSAMattributes Standard \
	 --readFilesIn $fastq_dir/"$SRA_ID".fastq

#STAR  with double fastq
STAR --genomeDir /opt/TAtlas/STAR_data/STAR_index/STAR_index_hg38_gtf_release_111/ \
	 --genomeLoad LoadAndKeep --runThreadN $(nproc) \
	 --outFileNamePrefix $star_dir/$SRA_ID/ \
	 --outSAMtype BAM SortedByCoordinate \
	 --outSAMunmapped Within \
	 --quantMode GeneCounts \
	 --limitBAMsortRAM 30064771072 \
	 --outSAMattributes Standard \
	 --readFilesIn $fastq_dir/"$SRA_ID"_1.fastq $fastq_dir/"$SRA_ID"_2.fastq

# DESeq2_STAR
Rscript /opt/TAtlas/DESeq2/STAR_count_normalization.R $SRA_ID


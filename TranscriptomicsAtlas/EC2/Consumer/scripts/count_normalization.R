#libraries
library(tximport)
library(readr)
suppressMessages(library(dplyr))
suppressMessages(library(DESeq2))

args <- commandArgs(trailingOnly = TRUE)
SRX <- args[1]

#bioproject name
stimulous = "stimulus"
control = "control"

# import salmon data to DESeq2
dir = "/home/ubuntu/salmon"
samples_all = read.table(file = "/home/ubuntu/DESeq2/samples.txt", header = TRUE,quote = '\t')
rownames(samples_all) = samples_all$run

samples = filter(samples_all, condition==paste(stimulous)|condition==paste(control))
files = file.path(dir, samples$run, "quant.sf")
names(files) = samples$run

tx2gene <- read_delim("/home/ubuntu/DESeq2/tx2gene.gencode.v42.csv", delim = ";", escape_double = FALSE, trim_ws = TRUE)

output_dir = "/istore/R_output/"
dir.create(output_dir)

txi = tximport(files, type="salmon", tx2gene=tx2gene)
write.csv2(txi, file = paste0(output_dir, SRX, "_salmon_rowcounts.csv", sep=""), row.names = TRUE, quote = FALSE)

dds = DESeqDataSetFromTximport(txi, colData = samples, design = ~1)
dds = estimateSizeFactors(object = dds)
normalized_counts = counts(dds, normalized=TRUE)
write.table(normalized_counts, file=paste0(output_dir, SRX, "_normalized_counts.txt", sep=""), sep="\t", quote=F, col.names=NA)

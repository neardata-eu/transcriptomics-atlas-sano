#libraries
library(tximport)
library(readr)
library(DESeq2)
library(dplyr)

#bioproject name

stimulous = "stimulus"
control = "control"
SRX="name"

#import salmon data to deSEQ2
dir = "C:/Users/sabin/.../genes"
samples_all = read.table(file = "samples_JJN3_without4.txt", header = TRUE,quote = '\t')
rownames(samples_all) = samples_all$run

samples_all
samples = filter(samples_all, condition==paste(stimulous)|condition==paste(control))
samples

files = file.path(dir, samples$run, "quant.sf")
names(files) = samples$run
files



tx2gene <- read_delim("tx2gene.gencode.v42.csv", 
                      delim = ";", escape_double = FALSE, trim_ws = TRUE)

txi = tximport(files, type="salmon", tx2gene=tx2gene)
write.csv2(txi, file = paste0(SRX,"_salmon_rowcounts.csv",sep=""), row.names = TRUE, quote = FALSE)


#normalization
dds = DESeqDataSetFromTximport(txi, colData = samples, design = ~ condition)
dds = estimate
SizeFactors(dds)
dds = estimateSizeFactors(object = dds)
normalized_counts = counts(dds, normalized=TRUE)
write.table(normalized_counts, file=paste0(SRX,"_normalized_counts.txt",sep=""), sep="\t", quote=F, col.names=NA)



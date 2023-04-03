#libraries
library(tximport)
library(readr)
library(DESeq2)
library(dplyr)

#bioproject name
stimulous = "stimulus"
control = "control"
SRX="SRR11858779"

# import salmon data to DESeq2
dir = "/home/ubuntu/salmon"
samples_all = read.table(file = "/home/ubuntu/DESeq2/samples.txt", header = TRUE,quote = '\t')
rownames(samples_all) = samples_all$run

samples = filter(samples_all, condition==paste(stimulous)|condition==paste(control))
files = file.path(dir, samples$run, "quant.sf")
names(files) = samples$run

tx2gene <- read_delim("/home/ubuntu/DESeq2/tx2gene.gencode.v42.csv", delim = ";", escape_double = FALSE, trim_ws = TRUE)

txi = tximport(files, type="salmon", tx2gene=tx2gene)
write.csv2(txi, file = paste0(SRX,"_salmon_rowcounts.csv",sep=""), row.names = TRUE, quote = FALSE)
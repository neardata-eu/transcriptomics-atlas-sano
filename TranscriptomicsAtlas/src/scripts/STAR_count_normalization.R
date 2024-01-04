library(data.table)
library(readr)
suppressMessages(library(dplyr))
suppressMessages(library(DESeq2))

args <- commandArgs(trailingOnly = TRUE)
SRX <- args[1]

input_dir = "/home/ubuntu/TAtlas/STAR"
output_dir = file.path("/home/ubuntu/TAtlas/R_output", SRX)
dir.create(output_dir)

#metadata
SRX_Ref = "SRR11982817"
stimulous = "stimulus"
control = "control"

#import file
ReadsPerGene_path <- file.path(input_dir, SRX, "ReadsPerGene.out.tab")
ReadPerGeneOut <- read_table(ReadsPerGene_path, skip = 4)
ReadPerGeneOut_Ref <- read_table("/opt/TAtlas/STAR_data/STAR_ref/SRR11982817-ref/ReadsPerGene.out.tab", skip = 4)

#create data frame
countData = as.data.frame(ReadPerGeneOut)[, c(1, 4)]

#add data from reference
countData = cbind(countData, as.data.frame(ReadPerGeneOut_Ref)[, 4])
colnames(countData) = c("transcript_ID", "stimulus", "control")

#define samples
samples_all = data.frame(samples = SRX, pop = 1.1, center = "HPC", run = SRX, condition = "stimulus")

#add control
samples_all = rbind(samples_all, data.frame(samples = SRX_Ref, pop = 1.1, center = "HPC", run = SRX_Ref, condition = "control"))

#write raw output
countData_export = select(countData, stimulus)
countData_export = cbind(countData[, 1], countData_export)
colnames(countData_export) = c("transcript_ID", "stimulus")

rowcounts_counts_filename = paste0(SRX, "_STAR_row_counts.csv")
rowcounts_counts_path = file.path(output_dir, rowcounts_counts_filename)
write.csv(countData_export, file = rowcounts_counts_path, quote=F, row.names = F)

#deseq
deseq_input = as.matrix(countData[, c(2:3)])
dds <- DESeqDataSetFromMatrix(countData = deseq_input, colData = samples_all, design = ~1)
dds = estimateSizeFactors(object = dds)

normalized_counts = as.data.frame(counts(dds, normalized = TRUE)) %>% select(stimulus)
normalized_counts = cbind(countData[, 1], normalized_counts)
colnames(normalized_counts) = c("transcript_ID", "stimulus")

#write normalized output
normalized_counts_filename = paste0(SRX, "_STAR_normalized_counts.txt")
normalized_counts_path = file.path(output_dir, normalized_counts_filename)
write.table(normalized_counts, file = normalized_counts_path, sep = "\t", quote = F, row.names = F)

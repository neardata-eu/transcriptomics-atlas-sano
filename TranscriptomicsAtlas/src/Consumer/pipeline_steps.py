import os
import re
import subprocess

import backoff

from config import my_env, work_dir, nproc, fastq_dir, salmon_dir, salmon_index_dir, star_index_dir, star_dir
from logger import log_output, logger
from utils import PipelineError


@backoff.on_exception(backoff.constant, Exception, max_tries=2, logger=logger)
@log_output
def prefetch(srr_id):
    prefetch_result = subprocess.run(
        ["prefetch", srr_id, "--min-size", "200m", "--max-size", "30g"],
        capture_output=True, text=True, env=my_env, cwd=work_dir
    )

    if "is smaller than minimum allowed: skipped" in prefetch_result.stderr:
        raise PipelineError(prefetch_result.stderr, "SRA file too small")
    elif "is larger than maximum allowed: skipped" in prefetch_result.stderr:
        raise PipelineError(prefetch_result.stderr, "SRA file too big")
    elif "Access denied - please request permission" in prefetch_result.stderr:
        raise PipelineError(prefetch_result.stderr, "SRA file not public")

    return prefetch_result


@backoff.on_exception(backoff.constant, Exception, max_tries=2, logger=logger)
@log_output
def fasterq_dump(srr_id, metadata=None):
    fasterq_result = subprocess.run(
        ["fasterq-dump", srr_id, "--outdir", fastq_dir, "--threads", nproc],
        capture_output=True, text=True, env=my_env, cwd=work_dir
    )

    if metadata:
        metadata["n_spots"] = int(fasterq_result.stderr.split("\n")[0].split(":")[1].strip().replace(",", ""))

    return fasterq_result


@log_output
def salmon(srr_id, metadata):
    salmon_cmd = ["salmon", "quant",
                  "--threads", nproc,
                  "-i", salmon_index_dir,
                  "--output", f"{salmon_dir}/{srr_id}",
                  "-l", "A",
                  "--useVBOpt"
                  ]

    if os.path.exists(f"{fastq_dir}/{srr_id}_1.fastq") and os.path.exists(f"{fastq_dir}/{srr_id}_2.fastq"):
        salmon_cmd.extend(["-1", f"{fastq_dir}/{srr_id}_1.fastq", "-2", f"{fastq_dir}/{srr_id}_2.fastq"])
        metadata["library_layout"] = "paired"
    elif os.path.exists(f"{fastq_dir}/{srr_id}.fastq"):
        salmon_cmd.extend(["-r", f"{fastq_dir}/{srr_id}.fastq"])
        metadata["library_layout"] = "single"
    else:
        raise PipelineError("Invalid library type. Couldn't find Paired on Single fastq.", "Invalid library type")

    salmon_result = subprocess.run(salmon_cmd, capture_output=True, text=True, env=my_env, cwd=work_dir)

    salmon_output = salmon_result.stderr
    if "Found no concordant and consistent mappings." in salmon_output:
        raise PipelineError(f"Found no concordant and consistent mappings for {srr_id}. Aborting the pipeline.",
                            "Found no concordant and consistent mappings")

    pattern = r'Mapping rate = (.*)%'
    match = re.search(pattern, salmon_output)
    if match:
        mapping_rate = float(match.group(1))
    else:
        raise PipelineError("Mapping rate not found. Aborting the pipeline.", "Mapping rate not found.")

    metadata["salmon_mapping_rate [%]"] = mapping_rate

    return salmon_result


@log_output
def load_star_index():
    cmd = ["STAR",
           "--genomeDir", star_index_dir,
           "--genomeLoad", "LoadAndExit",
           "--outFileNamePrefix", f"{work_dir}/STAR_load_index_log/",
           ]

    index_load_result = subprocess.run(cmd, capture_output=True, text=True, env=my_env, cwd=work_dir)

    return index_load_result


@log_output
def star(srr_id, metadata):
    star_cmd = ["STAR",
                "--genomeDir", star_index_dir,
                "--genomeLoad", "LoadAndKeep",
                "--runThreadN", nproc,
                "--outFileNamePrefix", f"{star_dir}/{srr_id}/",
                "--outSAMtype", "BAM", "SortedByCoordinate",
                "--outSAMunmapped", "Within",
                "--quantMode", "GeneCounts",
                "--limitBAMsortRAM", "30064771072",  # 28GiB
                "--outSAMattributes", "Standard"
                ]

    if os.path.exists(f"{fastq_dir}/{srr_id}_1.fastq") and os.path.exists(f"{fastq_dir}/{srr_id}_2.fastq"):
        star_cmd.extend(["--readFilesIn", f"{fastq_dir}/{srr_id}_1.fastq", f"{fastq_dir}/{srr_id}_2.fastq"])
        metadata["library_layout"] = "paired"
    elif os.path.exists(f"{fastq_dir}/{srr_id}.fastq"):
        star_cmd.extend(["--readFilesIn", f"{fastq_dir}/{srr_id}.fastq"])
        metadata["library_layout"] = "single"
    else:
        raise PipelineError("Invalid library type. Couldn't find Paired on Single fastq.", "Invalid library type")

    star_result = subprocess.run(star_cmd, capture_output=True, text=True, env=my_env, cwd=work_dir)

    log_final_path = f"{star_dir}/{srr_id}/Log.final.out"
    log_out_path = f"{star_dir}/{srr_id}/Log.out"
    if os.path.exists(log_out_path):
        with open(log_out_path) as f:
            logger.warning(f.read())

    if os.path.exists(log_final_path):
        with open(log_final_path) as f:
            logger.warning(f.read())

    with open(f"{star_dir}/{srr_id}/Log.final.out") as f:
        log_final = f.read()

    pattern = r"Uniquely mapped reads % \|(.*)%"
    match = re.search(pattern, log_final)
    mapping_rate = float(match.group(1).strip())
    metadata["STAR_mapping_rate [%]"] = mapping_rate

    return star_result


@log_output
def deseq2_star(srr_id):
    deseq2_result = subprocess.run(
        ["Rscript", "/opt/TAtlas/DESeq2/STAR_count_normalization.R", srr_id],
        capture_output=True, text=True, env=my_env, cwd=work_dir
    )

    return deseq2_result


@log_output
def deseq2_salmon(srr_id):
    deseq2_result = subprocess.run(
        ["Rscript", "/opt/TAtlas/DESeq2/Salmon_count_normalization.R", srr_id],
        capture_output=True, text=True, env=my_env, cwd=work_dir
    )

    return deseq2_result

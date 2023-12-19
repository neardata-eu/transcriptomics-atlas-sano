import os
import re
import subprocess

import backoff

from config import my_env, work_dir, nproc, fastq_dir
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

    return prefetch_result


@backoff.on_exception(backoff.constant, Exception, max_tries=2, logger=logger)
@log_output
def fasterq_dump(srr_id):
    fasterq_result = subprocess.run(
        ["fasterq-dump", srr_id, "--outdir", fastq_dir, "--threads", nproc],
        capture_output=True, text=True, env=my_env, cwd=work_dir
    )

    return fasterq_result


@log_output
def salmon(srr_id, metadata):
    index_path = "/opt/TAtlas/salmon_index/"
    quant_dir = f"/home/ubuntu/TAtlas/salmon/{srr_id}"
    os.makedirs(quant_dir, exist_ok=True)

    if os.path.exists(f"{fastq_dir}/{srr_id}.fastq"):
        salmon_result = subprocess.run(
            ["salmon", "quant", "--threads", nproc, "--useVBOpt", "-i", index_path, "-l", "A",
             "-r", f"{fastq_dir}/{srr_id}.fastq", "-o", quant_dir],
            capture_output=True, text=True, env=my_env, cwd=work_dir
        )
    else:
        salmon_result = subprocess.run(
            ["salmon", "quant", "--threads", nproc, "--useVBOpt", "-i", index_path, "-l", "A",
             "-1", f"{fastq_dir}/{srr_id}_1.fastq", "-2", f"{fastq_dir}/{srr_id}_2.fastq", "-o", quant_dir],
            capture_output=True, text=True, env=my_env, cwd=work_dir
        )

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
def deseq2_salmon(srr_id):
    deseq2_result = subprocess.run(
        ["Rscript", "/opt/TAtlas/DESeq2/Salmon_count_normalization.R", srr_id],
        capture_output=True, text=True, env=my_env, cwd=work_dir
    )

    return deseq2_result

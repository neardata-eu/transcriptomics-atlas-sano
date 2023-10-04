all: build_docker push_docker

build_docker:
	docker build -t piotrkica/salmonpipeline:backoff -f Dockerfile_salmon .

push_docker:
	docker push piotrkica/salmonpipeline:backoff

build_aws:
	docker build -t 542811361644.dkr.ecr.us-east-1.amazonaws.com/neardata_registry:salmon_pipeline -f Dockerfile_salmon .

push_aws:
	docker push 542811361644.dkr.ecr.us-east-1.amazonaws.com/neardata_registry:salmon_pipeline

sync-consumer:
	aws s3 sync src/Consumer s3://neardata-src/source/Consumer

sync-deseq2:
	aws s3 cp data/DESeq2/tx2gene.gencode.v42.csv s3://neardata-src/source/DESeq2/tx2gene.gencode.v42.csv
	aws s3 cp src/scripts/count_normalization.R s3://neardata-src/source/DESeq2/count_normalization.R

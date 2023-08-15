all: build push

build:
	docker build -t piotrkica/salmonpipeline:backoff -f Dockerfile_salmon .

push:
	docker push piotrkica/salmonpipeline:backoff

sync-consumer:
	aws s3 sync src/Consumer s3://neardata-bucket-1234/source/Consumer  # TODO update

sync-deseq2:
	aws s3 cp data/DESeq2/tx2gene.gencode.v42.csv s3://neardata-bucket-1234/source/DESeq2/tx2gene.gencode.v42.csv
	aws s3 cp src/scripts/count_normalization.R s3://neardata-bucket-1234/source/DESeq2/count_normalization.R
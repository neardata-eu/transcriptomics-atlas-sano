docker: build_docker push_docker

aws: auth_aws build_aws push_aws


### DOCKER ###
build_docker:
	docker build -t piotrkica/salmonpipeline:latest -f Dockerfile_salmon .

push_docker:
	docker push piotrkica/salmonpipeline:latest

### AWS ###
auth_aws:
	aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 542811361644.dkr.ecr.us-east-1.amazonaws.com/neardata_registry

build_aws:
	docker build -t 542811361644.dkr.ecr.us-east-1.amazonaws.com/neardata_registry:salmon_pipeline -f Dockerfile_salmon .

push_aws:
	docker push 542811361644.dkr.ecr.us-east-1.amazonaws.com/neardata_registry:salmon_pipeline

### SYNC SOURCE CODE ###
sync-consumer:
	aws s3 sync src/Consumer s3://neardata-src/source/Consumer

sync-salmon-deseq2:
	aws s3 cp data/DESeq2/tx2gene.gencode.v42.csv s3://neardata-src/source/DESeq2/tx2gene.gencode.v42.csv
	aws s3 cp src/scripts/Salmon_count_normalization.R s3://neardata-src/source/DESeq2/Salmon_count_normalization.R

### TEST CONTAINER ###
test:
	docker build -t salmon_test -f Dockerfile_test .
	docker run --mount type=bind,src="%cd%\\data\\salmon_index",dst="/opt/TAtlas/salmon_index" salmon_test

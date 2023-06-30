all: build push

build:
	docker build -t piotrkica/salmonpipeline:proc -f Dockerfile_salmon .

push:
	docker push piotrkica/salmonpipeline:proc
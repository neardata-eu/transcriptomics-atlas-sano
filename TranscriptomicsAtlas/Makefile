all: build push

build:
	docker build -t piotrkica/salmonpipeline:v2 -f Dockerfile_salmon .

push:
	docker push piotrkica/salmonpipeline:v2
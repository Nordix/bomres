REGISTRY ?= docker.io
REPOSITORY ?= bomres

prepare:
	@docker login $(REGISTRY)

build: 
	@make -C base_os    build 
	@make -C middleware build 
	@make -C service    build 

deploy:
	@make -C base_os deploy     REGISTRY=$(REGISTRY) REPOSITORY=$(REPOSITORY)
	@make -C middleware deploy  REGISTRY=$(REGISTRY) REPOSITORY=$(REPOSITORY)
	@make -C service deploy     REGISTRY=$(REGISTRY) REPOSITORY=$(REPOSITORY)


clean: 
	@make -C base_os clean 
	@make -C middleware clean 
	@make -C service clean 

cicd: prepare clean build deploy 


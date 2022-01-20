
REGISTRY ?= dr.t2data.com
REPOSITORY ?= resolver

build:
	@make -C build  build

deploy:
	@make -C deploy deploy  REGISTRY=$(REGISTRY) REPOSITORY=$(REPOSITORY)   

all: clean  build    deploy 

clean:
	@make -C build clean
	@make -C deploy clean

.PHONY: build
.PHONY: deploy

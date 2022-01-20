REGISTRY ?= sekidocker.rnd.ki.sw.ericsson.se
REPOSITORY ?= proj-mac-devopps

include build/config/settings




ext_build:
	@make -C build  build 

int_build:
	@make -C build  download 

deploy:
	@make -C deploy login   REGISTRY=$(REGISTRY)
	@make -C deploy deploy  REGISTRY=$(REGISTRY) REPOSITORY=$(REPOSITORY)   

all: clean  ext_build    deploy 

clean:
	@make -C build clean
	@make -C deploy clean

.PHONY: build
.PHONY: deploy

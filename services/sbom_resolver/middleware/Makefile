
include build/config/settings




build:
	@make -C build  build 

deploy:
	@make -C deploy deploy  REGISTRY=$(REGISTRY) REPOSITORY=$(REPOSITORY)   

all: clean  ext_build    deploy 

clean:
	@make -C build clean
	@make -C deploy clean

.PHONY: build
.PHONY: deploy

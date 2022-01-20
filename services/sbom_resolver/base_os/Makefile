
BASE_OS_IMAGE   = dr.t2data.com/resolver/base_os_alpine:3.15.12


prepare: 
	@docker run   --rm -it $(OPTIONS)  -v "$$PWD/build:/sandbox" -w /sandbox  -e IMAGE=$(BASE_OS_IMAGE) $(BASE_OS_IMAGE)  init
	@make -C build/base_os builder

ext_build: 
	@make -C build/base_os  public_build

int_build: 
	@make -C build/base_os  download
	@make -C build/base_os  private_build

build: prepare ext_build int_build

deploy:
	@make -C deploy deploy  REGISTRY=$(REGISTRY) REPOSITORY=$(REPOSITORY)


clean: 
	( cd build/base_os   && git clean -fd -fx  )	

.PHONY: build
.PHONY: deploy



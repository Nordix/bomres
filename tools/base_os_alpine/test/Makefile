DIR ?= build
include ../$(DIR)/config/settings


CONTAINER_IMAGE = $(BASE_OS_IMAGE):$(BASE_OS_VERSION)




# Invoke docker image with a shell for inspection 

sh:
	docker run -i -t    --entrypoint=/bin/sh $(CONTAINER_IMAGE) 

labels:
	@docker inspect  $(CONTAINER_IMAGE)  | jq .[0].ContainerConfig.Labels


test: 
	@docker run   --rm  -i --entrypoint='/usr/local/bin/bom.sh'  --name alpine$(ALPINE_VERSION) $(CONTAINER_IMAGE) | tee os.bom

clean:
	@rm -f os.bom

#
# Work in progress for rebuild 
# 
base: 
	docker run docker.io/bomres/base_os_alpine make > Makefile.base
	make -f Makefile.base config 
	echo grep >> alpine/build/base_os/config/packages  
	make -f Makefile.base build 
	make -f Makefile.base resolve
	make -f Makefile.base download_source

build: 
	docker build .  -f Containerfile -t abuild

abuild: 
	docker run -i -t -v $(PWD)/alpine/build/base_os/source/v3.14.3.x86_64:/aports  abuild:latest sh 


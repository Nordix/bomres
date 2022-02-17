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
	@rm -rf os.bom alpine apk pki  access_token Makefile.base

#
# Work in progress for rebuild 
# 

rebuild: base keygen build abuild 
base: 
	docker run docker.io/bomres/base_os_alpine make > Makefile.base
	make -f Makefile.base config 
	echo grep >> alpine/build/base_os/config/packages  
	make -f Makefile.base build 
	make -f Makefile.base resolve
	make -f Makefile.base download_source

keygen:
	mkdir -p pki 
	openssl genrsa -out pki/iafw.rsa 1024
	openssl rsa -in pki/iafw.rsa -pubout > pki/iafw.rsa.pub
	chmod 755 -R pki
build: 
	docker build .  -f Containerfile -t abuilder

abuild: 
	rm -rf apk 	
	mkdir -p apk
	docker run -i -t -v "$(PWD)/apk:/home/builder/packages" -v "$(PWD)/pki:/pki"  -v $(PWD)/alpine/build/base_os/source/repo:/aports  -v $(PWD)/builder:/root abuilder:latest sh 


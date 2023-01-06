#
#  Generate two containers 
#   1. Builder for Alpine base image 
#   2. Resolver for Alpine base image , Linux + Python  layer 


all: build push 

#  BUILD CONTAINERS 

build: base_os_alpine bom_resolver 

base_os_alpine: 
	make -C tools/base_os_alpine build

bom_resolver: bom_resolver_base_os  bom_resolver_service

bom_resolver_base_os:
	make -C services/sbom_resolver/base_os build

bom_resolver_service:
	make -C services/sbom_resolver/service/build build


#  PUSH CONTAINERS  

REGISTRY ?= docker.io
REPOSITORY ?= bomres

push: push_bom_resolver

push_bom_resolver:
	make -C services/sbom_resolver/service/deploy tag  REGISTRY=$(REGISTRY) REPOSITORY=$(REPOSITORY)
	make -C services/sbom_resolver/service/deploy push REGISTRY=$(REGISTRY) REPOSITORY=$(REPOSITORY)

push_base_os_alpine: 
	make -C tools/base_os_alpine/deploy  tag
	make -C tools/base_os_alpine/deploy  push


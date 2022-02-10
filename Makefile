

# Build on local host 

all: base_os_alpine bom_resolver 

base_os_alpine: 
	make -C tools/base_os_alpine local 

bom_resolver: bom_resolver_base_os  bom_resolver_service

bom_resolver_base_os:
	make -C services/sbom_resolver/base_os build

bom_resolver_service:
	make -C services/sbom_resolver/service build

clean: 
	make -C tools/base_os_alpine clean 

#  Push to container registry 

REGISTRY ?= docker.io
REPOSITORY ?= bomres

push: push_bom_resolver

push_bom_resolver:
	make -C services/sbom_resolver/service/deploy tag  REGISTRY=$(REGISTRY) REPOSITORY=$(REPOSITORY)
	make -C services/sbom_resolver/service/deploy push REGISTRY=$(REGISTRY) REPOSITORY=$(REPOSITORY)

#  Deploy on development k8 cluster 

deploy: 
	make -C services/sbom_resolver/service/deploy/k8_simple deploy

status: 
	make -C services/sbom_resolver/service/deploy/k8_simple status




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


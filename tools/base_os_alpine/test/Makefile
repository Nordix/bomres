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


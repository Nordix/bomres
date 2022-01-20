include ../build/base_os/config/settings

CONTAINER_IMAGE = $(BASE_OS_IMAGE):$(BASE_OS_VERSION)


tag:
	docker tag $(CONTAINER_IMAGE)  $(REGISTRY)/$(REPOSITORY)/$(CONTAINER_IMAGE) 

login:
	docker login $(REGISTRY)

push:
	docker push $(REGISTRY)/$(REPOSITORY)/$(CONTAINER_IMAGE)

deploy:  tag  push 

clean:


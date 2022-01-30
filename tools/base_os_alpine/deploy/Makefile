DIR ?=build


REGISTRY=docker.io
REPOSITORY=bomres


include  ../$(DIR)/config/settings


CONTAINER_IMAGE = $(BASE_OS_IMAGE):$(BASE_OS_VERSION)
LATEST_CONTAINER_IMAGE = $(BASE_OS_IMAGE):latest

clean:

tag:
	docker tag $(CONTAINER_IMAGE) $(REGISTRY)/$(REPOSITORY)/$(CONTAINER_IMAGE)
	docker tag $(CONTAINER_IMAGE) $(REGISTRY)/$(REPOSITORY)/$(LATEST_CONTAINER_IMAGE)

login:
	docker login $(REGISTRY)

push:
	docker push $(REGISTRY)/$(REPOSITORY)/$(CONTAINER_IMAGE)
	docker push $(REGISTRY)/$(REPOSITORY)/$(LATEST_CONTAINER_IMAGE)

deploy:  tag  push 



include ../build/config/settings


tag:
	docker tag $(SERVICE_IMAGE):$(SERVICE_VERSION) $(REGISTRY)/$(REPOSITORY)/$(SERVICE_IMAGE):$(SERVICE_VERSION) 
	docker tag $(SERVICE_IMAGE):$(SERVICE_VERSION) $(REGISTRY)/$(REPOSITORY)/$(SERVICE_IMAGE):latest 

login:
	docker login $(REGISTRY)

push:
	docker push $(REGISTRY)/$(REPOSITORY)/$(SERVICE_IMAGE):$(SERVICE_VERSION)
	docker push $(REGISTRY)/$(REPOSITORY)/$(SERVICE_IMAGE):latest

deploy:  tag  push 

clean:



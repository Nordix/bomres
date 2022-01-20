include ../build/config/settings


tag:
	docker tag $(MIDDLEWARE_IMAGE):$(MIDDLEWARE_VERSION) $(REGISTRY)/$(REPOSITORY)/$(MIDDLEWARE_IMAGE):$(MIDDLEWARE_VERSION) 

login:
	docker login $(REGISTRY)

push:
	docker push $(REGISTRY)/$(REPOSITORY)/$(MIDDLEWARE_IMAGE):$(MIDDLEWARE_VERSION)

deploy:  tag  push 

clean:


include ../build/config/settings

REGISTRY ?= dr.t2data.com
REPOSITORY ?= resolver



tag:
	docker tag $(MIDDLEWARE_IMAGE):$(MIDDLEWARE_VERSION) $(REGISTRY)/$(REPOSITORY)/$(MIDDLEWARE_IMAGE):$(MIDDLEWARE_VERSION) 

login:
	docker login $(REGISTRY)

push:
	docker push $(REGISTRY)/$(REPOSITORY)/$(MIDDLEWARE_IMAGE):$(MIDDLEWARE_VERSION)

deploy:  tag  push 

clean:


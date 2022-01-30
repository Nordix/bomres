include ../build/config/settings

REGISTRY ?= docker.io
REPOSITORY ?= bomres



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



#  Kubernetes
#    There is two directories for deployment in Kubernetes
#     k8_simple: Yaml files for deployment with kubectl and Make
#     k8_helm:   Helm charts

K8_DEPLOY = k8_simple

kube_deploy:
	make -C $(K8_DEPLOY)  deploy

kube_delete:
	make -C $(K8_DEPLOY)   delete

kube_status:
	make -C $(K8_DEPLOY) status







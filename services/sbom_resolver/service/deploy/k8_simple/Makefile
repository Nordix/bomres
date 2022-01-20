#
#  Kubernetes 
#

PROJECT=sbom-resolver
NAMESPACE=default


KUBE_CONFIG = --kubeconfig=$$HOME/.kube/t2
KUBECTL = kubectl $(KUBE_CONFIG)
POD = $(shell $(KUBECTL) get  pods   | grep $(PROJECT)-  | awk '{print $$1}' | head -1 )



# kubectl --kubeconfig=$HOME/.kube/t2 apply -f sbom-resolver-volume_cache.yaml
# kubectl --kubeconfig=$HOME/.kube/t2 apply -f sbom-resolver-volume-claim_cache.yaml



status:
	@$(KUBECTL) get pods  -n $(NAMESPACE)
	@$(KUBECTL) get  pv  bomresolver-cache -n $(NAMESPACE) 
	@$(KUBECTL) get  pvc bomresolver-storage-cache -n $(NAMESPACE)

log:
	@$(KUBECTL) logs $(POD)  -n $(NAMESPACE)  -f

desc:
	@$(KUBECTL) describe pod  $(POD)  -n $(NAMESPACE)

deploy:
	@$(KUBECTL) apply -f $(PROJECT).yaml  -n $(NAMESPACE)
	@$(KUBECTL) apply -f ingress.yaml   -n $(NAMESPACE)

delete: 
	@$(KUBECTL) delete deployments  $(PROJECT)  -n $(NAMESPACE) || exit 0
	@$(KUBECTL) delete ingress   $(PROJECT)  -n $(NAMESPACE) || exit 0

delete_volume:
	@$(KUBECTL)  delete pvc bomresolver-storage-cache || exit 0
	@$(KUBECTL)  delete pv  bomresolver-cache || exit 0

deploy_volume:
	@$(KUBECTL)  apply -f sbom-resolver-volume_cache.yaml
	@$(KUBECTL)  apply -f sbom-resolver-volume-claim_cache.yaml

shell:
	@$(KUBECTL)  exec -i -t  -n $(NAMESPACE)   $(POD) sh

pull_secret:
	@$(KUBECTL) create secret docker-registry regcred --docker-server=$(REGISTRY) --docker-username=$(DOCKER_USERNAME) --docker-password=$(DOCKER_PASSWORD) -n $(NAMESPACE)




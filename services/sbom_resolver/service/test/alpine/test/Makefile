DIR ?= build
include ../build/base_os/config/settings


CONTAINER_IMAGE = $(BASE_OS_IMAGE):$(BASE_OS_VERSION)




# Invoke docker image with a shell for inspection 

sh:
	docker run -i -t    --entrypoint=/bin/sh $(CONTAINER_IMAGE) 

labels:
	@docker inspect  $(CONTAINER_IMAGE)  | jq .[0].ContainerConfig.Labels


test: labels
	@docker run   --rm  -i --entrypoint='/usr/local/bin/bom.sh'  --name alpine$(ALPINE_VERSION) $(CONTAINER_IMAGE) | tee os.bom


PWD = $(CURDIR)
#SCAN_OPTIONS =  
#SCAN_OPTIONS = --skip-update 
SCAN_OPTIONS = -f json -o /report/results.json

cve_scan: 
	mkdir -p trivy/cache && mkdir -p trivy/report
	docker run --privileged --rm -v /run/user/1001/docker.sock:/var/run/docker.sock \
                             -v $(PWD)/trivy/cache:/root/.cache/ \
                             -v $(PWD)/trivy/report:/report \
			     aquasec/trivy:latest $(SCAN_OPTIONS)   $(CONTAINER_IMAGE)

clean:
	@rm -rf os.bom trivy
	@rm -rf syft.spdx


# curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh -s -- -b /usr/local/bin
syft: 

	#syft $(ONTAINER_IMAGE)   --scope all-layers  | tee syft.txt
	#syft $(ONTAINER_IMAGE)   -o cyclonedx | tee syft.xml
	syft $(CONTAINER_IMAGE)   -o spdx | tee syft.spdx


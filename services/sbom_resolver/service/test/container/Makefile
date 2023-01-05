#
# Work in progress , dont expect this to work 
#

TOOLS_REPO      = docker.io/bomres
ALPINE_BUILDER  = base_os_alpine:latest
BASE_OS_IMAGE   = $(TOOLS_REPO)/$(ALPINE_BUILDER)

include ../../build/config/settings
CONTAINER_IMAGE = $(SERVICE_IMAGE):$(SERVICE_VERSION)

save: 
	mkdir -p $(DIR)/tools/images
	rm -f $(DIR)/tools/images/$(ALPINE_BUILDER).tar 
	docker save $(BASE_OS_IMAGE) > $(DIR)/tools/images/$(ALPINE_BUILDER).tar 

load: 
	docker load <  $(DIR)/tools/images/$(ALPINE_BUILDER).tar 


DIR=alpine


container_aggregate: 
	@docker run   --rm -it $(OPTIONS)  -v "$$PWD/$(DIR)/build:/sandbox"  -e IMAGE=$(BASE_OS_IMAGE) $(BASE_OS_IMAGE)  aggregate

python_aggregate:
	python3  ../build/bomres/bomres/lib/aggregate_bom.py  --pkgindex $(PWD)/$(DIR)/build/base_os/sbom/apkindex.tar    --desired $(PWD)/$(DIR)/build/base_os/sbom/os.conf  \
                          --resolved $(PWD)/$(DIR)/build/base_os/sbom/os.bom  --config $(PWD)/$(DIR)/build/base_os/config/settings  --output $(PWD)/$(DIR)/build/base_os/sbom/aggregated.json #  --debug




clone: 
	docker run -i -t -v  /tmp/alpine/src:/mnt/alpine/src    $(CONTAINER_IMAGE) clone 


index:
	docker run -i -t -v "$$PWD/$(DIR)/build/base_os/sbom:/sbom" -v  "/tmp/alpine/src:/mnt/alpine/src" -v  "/tmp/alpine/checkout:/mnt/alpine/checkout"  -v  "/tmp/alpine/cache:/mnt/alpine/cache" $(CONTAINER_IMAGE) index

resolve: 
	docker run -i -t -v "$$PWD/$(DIR)/build/base_os/sbom:/sbom"  -v "/tmp/alpine/cache:/mnt/alpine/cache"  $(CONTAINER_IMAGE) resolve

# This is fast when running as a tool  
retrieve_patches:
	docker run -i -t -v "$$PWD/$(DIR)/build/base_os/sbom:/sbom" -v "/tmp/alpine/src:/mnt/alpine/src" -v "$$PWD/$(DIR)/build/base_os/source:/source"  $(CONTAINER_IMAGE) download internal


# This may take long time 
retrieve_source:
	docker run -i -t -v "$$PWD/$(DIR)/build/base_os/sbom:/sbom" -v "/tmp/alpine/src:/mnt/alpine/src" -v "$$PWD/$(DIR)/build/base_os/source:/source"  $(CONTAINER_IMAGE) download external



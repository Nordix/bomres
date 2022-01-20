include ../../base_os/build/base_os/config/settings

include config/settings

CONTAINER_TOOL=docker

CONTAINER_IMAGE = $(MIDDLEWARE_IMAGE):$(MIDDLEWARE_VERSION)
BASE_OS=$(BASE_OS_IMAGE):$(BASE_OS_VERSION) 


pip:
	$(CONTAINER_TOOL) build -t  $(CONTAINER_IMAGE) --build-arg BASE_OS_IMAGE=$(BASE_OS)  -f Containerfile . 

build: pip
	mkdir -p sbom 
	cp config/packages sbom/requirement.txt
	$(CONTAINER_TOOL) run -i -t   ${CONTAINER_IMAGE} pip3 freeze | tee sbom/requirement.freeze
	$(CONTAINER_TOOL) run -i -t   ${CONTAINER_IMAGE} pip3 list --format json  | tee sbom/packages.json 

download: 
	mkdir -p source 
	$(CONTAINER_TOOL) run -i -t -v "$$PWD/source:/packages"   ${CONTAINER_IMAGE}  pip3 download -r requirement.txt --dest  /packages --no-binary :all:

shell: 
	$(CONTAINER_TOOL) run -i -t  --entrypoint=/bin/bash ${CONTAINER_IMAGE}


# curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh -s -- -b /usr/local/bin
spdx: 
	syft $(CONTAINER_IMAGE)   -o spdx | tee syft.spdx

clean: 
	@rm -rf source sbom  syft.spdx



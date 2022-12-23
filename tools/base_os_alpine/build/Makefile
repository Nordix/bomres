include config/settings

CONTAINER_IMAGE = $(BASE_OS_IMAGE):$(BASE_OS_VERSION)



BUILD_DIR = payload_dir
BUILDER_DIR = build_dir
BUILD_CONTAINER_FILE = $(BUILDER_DIR)/Containerfile

CWD := $(shell cd -P -- '$(shell dirname -- "$0")' && pwd -P)

.PHONY: $(BUILD_CONTAINER_FILE)
.PHONY: download
.PHONY: $(PAYLOAD_CONTAINER_FILE)

clean:
	rm -rf $(BUILD_DIR)
	rm -rf $(BUILDER_DIR)
	rm -rf sbom
	rm -rf download download.bash


$(BUILD_CONTAINER_FILE) :
	mkdir -p $(BUILDER_DIR)/scripts
	cp  scripts/* $(BUILDER_DIR)/scripts
	echo "FROM alpine:$(ALPINE_VERSION)" > $@
	echo "COPY scripts/mkimage-alpine.bash scripts/apk-install /" >> $@
	echo "RUN /apk-install bash tzdata xz curl" >> $@
	echo "ENTRYPOINT [\"/mkimage-alpine.bash\"]"  >> $@

# Create the Alpine build image
builder:   $(BUILD_CONTAINER_FILE)
	cd $(BUILDER_DIR) && docker build -t ${BUILDER_IMAGE} -f Containerfile .


PAYLOAD_CONTAINER_FILE = $(BUILD_DIR)/Containerfile

PACKAGE_LIST  =$(shell test -f config/packages &&  cat config/packages  |  grep -v '\#' |  awk -vORS=, '{ print $$1 }' | sed 's/,$$/\n/' )

$(PAYLOAD_CONTAINER_FILE) :
	mkdir -p $(BUILD_DIR)/scripts
	mkdir -p $(BUILD_DIR)/templates
	mkdir -p sbom
	cp docker-entrypoint.sh  $(BUILD_DIR)/docker-entrypoint.sh
	cp  scripts/* $(BUILD_DIR)/scripts
	cp  -f -r templates/* $(BUILD_DIR)/templates
	echo "FROM scratch" > $@
	echo 'LABEL org.opencontainers.image.title=$(IMAGE_TITLE)' >> $@
	echo 'LABEL org.opencontainers.image.created=$(IMAGE_CREATED)' >> $@
	echo 'LABEL org.opencontainers.image.revision=$(IMAGE_REVISION)' >> $@
	echo 'LABEL org.opencontainers.image.vendor=$(IMAGE_VENDOR)' >> $@
	echo 'LABEL org.opencontainers.image.version=$(IMAGE_VERSION)' >> $@
	echo 'LABEL org.opencontainers.image.authors=$(IMAGE_AUTHOR)' >> $@
	echo "ADD rootfs.tar.gz /" >> $@
	echo "COPY scripts/bom.sh /usr/local/bin/bom.sh " >> $@
	echo "RUN chmod 755 /usr/local/bin/bom.sh" >> $@
	echo "COPY docker-entrypoint.sh / " >> $@
	echo "RUN chmod 755 /docker-entrypoint.sh" >> $@
	echo "COPY templates/ /opt/base_os/templates/" >> $@
	echo "COPY scripts/ /opt/base_os/scripts/" >> $@
	echo "RUN chmod -R 755 /opt/base_os" >> $@
	echo "ENTRYPOINT [\"/docker-entrypoint.sh\"]" >> $@
	echo 'CMD ["help"]' >> $@




public_build:  $(PAYLOAD_CONTAINER_FILE)
	docker run --rm -v$(CWD)/$(BUILD_DIR):/rootfs $(BUILDER_IMAGE) -a $(ARCH)  -b -s -t UTC -r v$(ALPINE_VERSION) -m $(REPO_URL)  -p $(PACKAGE_LIST)  
	cd $(BUILD_DIR) && docker build -t $(CONTAINER_IMAGE) -f Containerfile .
	docker run --rm -i  $(CONTAINER_IMAGE)  /bin/sh -c 'apk info -v 2> /dev/null' > sbom/os.apk

private_build:  $(PAYLOAD_CONTAINER_FILE)
	docker run -v "$$PWD/download/alpine/:/download"  --rm $(BUILDER_IMAGE)  -a  $(ARCH)  -b -s -t UTC -r v$(ALPINE_VERSION) -m /download -p $(PACKAGE_LIST)   > $(BUILD_DIR)/rootfs.tar.gz
	cd $(BUILD_DIR) && docker build -t $(CONTAINER_IMAGE)  -f Containerfile  .
	docker run --rm -i   $(CONTAINER_IMAGE)  /bin/sh -c '/usr/local/bin/bom.sh 2> /dev/null' > sbom/os.bom
	cat config/packages > sbom/os.conf


download:
	@cp scripts/download.bash . 
	@bash download.bash




# build:
#	docker build -t  $(CONTAINER_IMAGE) .


# Invoke docker image with a shell for inspection 

docker_test:
	docker run -i -t    --entrypoint=/bin/sh $(CONTAINER_IMAGE) 

cpe:
	@docker run   --rm  -i --entrypoint='/usr/local/bin/bom.sh'  --name alpine$(ALPINE_VERSION) $(CONTAINER_IMAGE) | tee os.bom



tag:
	docker tag $(CONTAINER_IMAGE) $(REGISTRY)/$(REPOSITORY)/$(CONTAINER_IMAGE)

login:
	docker login $(REGISTRY)

push:
	docker push $(REGISTRY)/$(REPOSITORY)/$(CONTAINER_IMAGE)

release: build  tag login push 




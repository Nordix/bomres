#
#  tools/base_os_alpine/build/templates/makefiles/Makefile
#
#  This file is written to stdout out by the command below
#  podman run docker.io/bomres/base_os_alpine init
#

include config/settings

BUILDER_IMAGE=alpine_builder

BUILDER_DIR = build_dir
BUILD_DIR = payload_dir
BUILD_CONTAINER_FILE = $(BUILDER_DIR)/Containerfile

CWD := $(shell cd -P -- '$(shell dirname -- "$0")' && pwd -P)


CONTAINER_IMAGE = $(BASE_OS_IMAGE):$(BASE_OS_VERSION)



.PHONY: $(BUILD_CONTAINER_FILE)
.PHONY: download
$(BUILD_CONTAINER_FILE) :
	echo "FROM alpine:$(ALPINE_VERSION)" > $@
	echo "COPY scripts/mkimage-alpine.bash scripts/apk-install /" >> $@
	echo "RUN /apk-install bash tzdata xz curl" >> $@
	echo "ENTRYPOINT [\"/mkimage-alpine.bash\"]"  >> $@


PAYLOAD_CONTAINER_FILE = $(BUILD_DIR)/Containerfile

PACKAGE_LIST  =$(shell test -f config/packages &&  cat config/packages  |  grep -v '^\#' |  awk -vORS=, '{ print $$1 }' | sed 's/,$$/\n/' )

.PHONY: $(PAYLOAD_CONTAINER_FILE)
$(PAYLOAD_CONTAINER_FILE) :
	echo "FROM scratch" > $@
	echo 'LABEL org.opencontainers.image.title=$(IMAGE_TITLE)' >> $@
	echo 'LABEL org.opencontainers.image.created=$(IMAGE_CREATED)' >> $@
	echo 'LABEL org.opencontainers.image.revision=$(IMAGE_REVISION)' >> $@
	echo 'LABEL org.opencontainers.image.vendor=$(IMAGE_VENDOR)' >> $@
	echo 'LABEL org.opencontainers.image.version=$(IMAGE_VERSION)' >> $@
	echo 'LABEL org.opencontainers.image.authors=$(IMAGE_AUTHOR)' >> $@
	echo "ADD rootfs.tar.gz /" >> $@
	echo "COPY scripts/bom.sh /usr/local/bin/bom.sh " >> $@
	echo "RUN chmod u+x,g+x,o+x /usr/local/bin/bom.sh" >> $@
	echo 'CMD ["/bin/sh"]' >> $@


# Create the Alpine build image 
builder:  clean $(BUILD_CONTAINER_FILE)
	cd $(BUILDER_DIR) && podman build -t ${BUILDER_IMAGE} -f Containerfile .
	mkdir -p tools
	rm -f tools/${BUILDER_IMAGE}.tar
	podman save ${BUILDER_IMAGE} -o tools/${BUILDER_IMAGE}.tar 


load_builder:
	podman load <  tools/${BUILDER_IMAGE}.tar 
	

clean:
	-podman rmi --force ${BUILDER_IMAGE}

# Test the newly created build image by invoke a shell in the container 
test_builder:
	podman run -i -t -v$(CWD)/$(BUILD_DIR):/rootfs  --entrypoint=/bin/bash ${BUILDER_IMAGE} 




public_build:  $(PAYLOAD_CONTAINER_FILE)
	podman run -v$(CWD)/$(BUILD_DIR):/rootfs --rm $(BUILDER_IMAGE) -a $(ARCH)  -b -s -t UTC -r v$(ALPINE_VERSION) -m $(REPO_URL)  -p $(PACKAGE_LIST)  
	cd $(BUILD_DIR) && podman build -t $(CONTAINER_IMAGE) -f Containerfile .
	podman run --rm -i  $(CONTAINER_IMAGE)  /bin/sh -c 'apk info -v 2> /dev/null' > sbom/os.apk

private_build:  $(PAYLOAD_CONTAINER_FILE)
	podman run -v$(CWD)/$(BUILD_DIR):/rootfs  -v "$(CWD)/download/alpine/:/download"  --rm $(BUILDER_IMAGE)  -a  $(ARCH)   -b -s -t UTC -r v$(ALPINE_VERSION) -m /download -p $(PACKAGE_LIST)  
	cd $(BUILD_DIR) && podman build -t $(CONTAINER_IMAGE) -f Containerfile .
	podman run --rm -i  $(CONTAINER_IMAGE) /bin/sh -c '/usr/local/bin/bom.sh 2> /dev/null' > sbom/os.bom
	cat config/packages  > sbom/os.conf	


tag:
	podman tag $(CONTAINER_IMAGE) $(REGISTRY)/$(REPOSITORY)/$(CONTAINER_IMAGE)

login:
	podman login $(REGISTRY)

push:
	podman push $(REGISTRY)/$(REPOSITORY)/$(CONTAINER_IMAGE)


download:
	@bash download.bash

prepare: login builder public_build  
build:   private_build tag  push

test_payload:
	podman run -i -t --entrypoint=/bin/sh   $(REGISTRY)/$(REPOSITORY)/$(PAYLOAD_IMAGE):$(BASE_VERSION)

# mount -t proc proc /proc
chroot_payload:
	sudo mkdir -p rootfs 
	sudo tar xvxf $(BUILD_DIR)/rootfs.tar.gz -C rootfs 
	sudo chroot rootfs /bin/sh



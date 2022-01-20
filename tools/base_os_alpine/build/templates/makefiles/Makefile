include config/settings

BUILDER_IMAGE=alpine_builder

BUILDER_DIR = build_dir
BUILD_DIR = payload_dir
BUILD_CONTAINER_FILE = $(BUILDER_DIR)/Containerfile


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
	cd $(BUILDER_DIR) && docker build -t ${BUILDER_IMAGE} -f Containerfile .
	mkdir -p tools
	docker save ${BUILDER_IMAGE} -o tools/${BUILDER_IMAGE}.tar 


load_builder:
	docker load <  tools/${BUILDER_IMAGE}.tar 
	

clean:
	-docker rmi --force ${BUILDER_IMAGE}

# Test the newly created build image by invoke a shell in the container 
test_builder:
	docker run -i -t -v "$$PWD/packages/alpine:/packages"  --entrypoint=/bin/bash ${BUILDER_IMAGE} 




public_build:  $(PAYLOAD_CONTAINER_FILE)
	docker run --rm $(BUILDER_IMAGE) -a $(ARCH)  -b -s -t UTC -r v$(ALPINE_VERSION) -m $(REPO_URL)  -p $(PACKAGE_LIST)   > $(BUILD_DIR)/rootfs.tar.gz
	cd $(BUILD_DIR) && docker build -t $(CONTAINER_IMAGE) -f Containerfile .
	docker run --rm -i  --name alpine$(ALPINE_VERSION) $(CONTAINER_IMAGE)  /bin/sh -c 'apk info -v 2> /dev/null' > sbom/os.apk
	dos2unix sbom/os.apk

private_build:  $(PAYLOAD_CONTAINER_FILE)
	docker run -v "$$PWD/download/alpine/:/download"  --rm $(BUILDER_IMAGE)  -a  $(ARCH)   -b -s -t UTC -r v$(ALPINE_VERSION) -m /download -p $(PACKAGE_LIST)   > $(BUILD_DIR)/rootfs.tar.gz
	cd $(BUILD_DIR) && docker build -t $(CONTAINER_IMAGE) -f Containerfile .
	docker run --rm -i  --name alpine$(ALPINE_VERSION) $(CONTAINER_IMAGE) /bin/sh -c '/usr/local/bin/bom.sh 2> /dev/null' > sbom/os.bom
	cat config/packages  > sbom/os.conf	


tag:
	docker tag $(CONTAINER_IMAGE) $(REGISTRY)/$(REPOSITORY)/$(CONTAINER_IMAGE)

login:
	docker login $(REGISTRY)

push:
	docker push $(REGISTRY)/$(REPOSITORY)/$(CONTAINER_IMAGE)


download:
	@bash download.bash

prepare: login builder public_build  
build:   private_build tag  push

test_payload:
	docker run -i -t --entrypoint=/bin/sh   $(REGISTRY)/$(REPOSITORY)/$(PAYLOAD_IMAGE):$(BASE_VERSION)

# mount -t proc proc /proc
chroot_payload:
	sudo mkdir -p rootfs 
	sudo tar xvxf $(BUILD_DIR)/rootfs.tar.gz -C rootfs 
	sudo chroot rootfs /bin/sh





BASE_OS_IMAGE   = docker.io/bomres/base_os_alpine
RESOLVER_IMAGE  = docker.io/bomres/alpine_resolver
TOOLS_IMAGE  = alpine_sandbox_base_os_tool:3.15.1

DIR=product
TEMPDIR=/tmp/alpine


help:
	@echo ""
	@echo "Build reference image"
	@echo "make config && vim product/build/base_os/config/packages && make init && make prepare"
	@echo ""
	@echo ""

_config:
	@docker run   --rm -it $(OPTIONS)  -v "$$PWD/$(DIR)/build:/sandbox" -w /sandbox  -e IMAGE=$(BASE_OS_IMAGE) $(BASE_OS_IMAGE)  config


_init:
	@docker run   --rm -it $(OPTIONS)  -v "$$PWD/$(DIR)/build:/sandbox" -w /sandbox  -e IMAGE=$(BASE_OS_IMAGE) $(BASE_OS_IMAGE)  init


_prepare:
	@make -C $$PWD/$(DIR)/build/base_os  builder

_public_build:
	@make -C $$PWD/$(DIR)/build/base_os  public_build

_download:
	@make -C  $$PWD/$(DIR)/build/base_os  download

_private_build:
	@make -C $$PWD/$(DIR)/build/base_os  private_build

_test: 
	@make $(TEST_MAKEFILE)  DIR=$(DIR)
	@make -C $$PWD/$(DIR)/test  test DIR=$(DIR)

_sh: 
	@make $(TEST_MAKEFILE)  DIR=$(DIR)
	@make -C $$PWD/$(DIR)/test  sh DIR=$(DIR)

_aggregate: 
	@docker run   --rm -it $(OPTIONS)  -v "$$PWD/$(DIR)/build:/sandbox"  $(BASE_OS_IMAGE)  aggregate

aggregate: 
	make _aggregate DIR=product
config: 
	make _config DIR=product
init: 
	make _init DIR=product
public_build: 
	make _public_build DIR=product
prepare: 
	make _prepare DIR=product
download: 
	make _download DIR=product
private_build: 
	make _private_build DIR=product
test: 
	make _test DIR=product
sh: 
	make _sh DIR=product
res: 
	make _res DIR=product
index: 
	make _index DIR=product


clone: 
	docker run -i -t -v  $(TEMPDIR)/src:/mnt/alpine/src    $(RESOLVER_IMAGE) clone 

_index:
	docker run -i -t -v "$$PWD/$(DIR)/build/base_os/sbom:/sbom" -v  "$(TEMPDIR)/src:/mnt/alpine/src" -v  "$(TEMPDIR)/checkout:/mnt/alpine/checkout"  -v  "$(TEMPDIR)/cache:/mnt/alpine/cache" $(RESOLVER_IMAGE) index

_res: 
	docker run -i -t -v "$$PWD/$(DIR)/build/base_os/sbom:/sbom"  -v "$(TEMPDIR)/cache:/mnt/alpine/cache"  $(RESOLVER_IMAGE) resolve

_download_source:
	docker run -i -t -v "$$PWD/$(DIR)/build/base_os/sbom:/sbom" -v "$(TEMPDIR)/src:/mnt/alpine/src" -v "$$PWD/$(DIR)/build/base_os/source:/source"  $(RESOLVER_IMAGE) download internal patch
	docker run -i -t -v "$$PWD/$(DIR)/build/base_os/sbom:/sbom" -v "$(TEMPDIR)/src:/mnt/alpine/src" -v "$$PWD/$(DIR)/build/base_os/source:/source"  $(RESOLVER_IMAGE) download internal code
	docker run -i -t -v "$$PWD/$(DIR)/build/base_os/sbom:/sbom" -v "$(TEMPDIR)/src:/mnt/alpine/src" -v "$$PWD/$(DIR)/build/base_os/source:/source"  $(RESOLVER_IMAGE) download internal build
	docker run -i -t -v "$$PWD/$(DIR)/build/base_os/sbom:/sbom" -v "$(TEMPDIR)/src:/mnt/alpine/src" -v "$$PWD/$(DIR)/build/base_os/source:/source"  $(RESOLVER_IMAGE) download external patch
	docker run -i -t -v "$$PWD/$(DIR)/build/base_os/sbom:/sbom" -v "$(TEMPDIR)/src:/mnt/alpine/src" -v "$$PWD/$(DIR)/build/base_os/source:/source"  $(RESOLVER_IMAGE) download external code


p_build: init config prepare public_build download private_build test aggregate
p_resolve: clone index res 


download_source:
	make _download_source DIR=product

.PHONY: tool
tool_config:
	@mkdir -p tool/build/base_os/config/
	@docker run   --rm -it  -v "$$PWD/product/build/base_os/sbom:/sbom"  $(RESOLVER_IMAGE) tool packages > tool/build/base_os/config/packages
	@docker run   --rm -it  -v "$$PWD/product/build/base_os/sbom:/sbom"  $(RESOLVER_IMAGE) tool settings > tool/build/base_os/config/settings
	@dos2unix tool/build/base_os/config/packages 
	@dos2unix tool/build/base_os/config/settings


tool_init: 
	make _init DIR=tool
tool_prepare: 
	make _prepare DIR=tool

tool_public_build: 
	make _public_build DIR=tool

tool_test: 
	make _test DIR=test

tool_download: 
	make _download DIR=tool
tool_private_build: 
	make _private_build DIR=tool
tool_aggregate: 
	make _aggregate DIR=tool
tool_index: 
	make _index DIR=tool
tool_res: 
	make _res DIR=tool

tool_download_source:
	make _download_source DIR=tool

tool_build: tool_config tool_init tool_prepare tool_public_build tool/builder/Makefile # check  keygen pkg
tool_resolve: clone tool_index tool_res 

PACKAGE=prometheus-node-exporter
REPO=community

abuild: 
	docker run -i -t -v "$(PWD)/tool/apk:/var/local/packages" -v "$(PWD)/tool/pki:/pki"  -v $(PWD)/product/build/base_os/source/repo:/aports  -v $(PWD)/tool/builder:/root $(TOOLS_IMAGE)  make -C /root build PACKAGE=$(PACKAGE) ARCH=$(ARCH) REPO=$(REPO) 

shell:
	docker run -i -t  -v "$$PWD/tool/download/alpine/:/download"  -v "$(PWD)/apk:/var/local/packages" -v "$(PWD)/tool/pki:/pki"  -v $(PWD)/product/build/base_os/source/repo:/aports  -v $(PWD)/tool/builder:/root $(TOOLS_IMAGE) sh 


REPOS =  $(shell ls product/build/base_os/source/repo )

ECHO      = $(shell which echo 2> /dev/null)
ARCH=x86_64

VERIFY_LOG=verify.log

check:
	rm -f $(VERIFY_LOG)
	@for repo in ${REPOS};                   \
	do                                      \
	for i in `ls product/build/base_os/source/repo/$${repo}`;             \
	do                                  \
		if docker run -i -t -v "$(PWD)/tool/apk:/var/local/packages" -v "$(PWD)/tool/pki:/pki"  -v $(PWD)/product/build/base_os/source/repo:/aports  -v $(PWD)/tool/builder:/root $(TOOLS_IMAGE) make -C /root check ARCH=${ARCH} PACKAGE=$${i} REPO=$${repo} ; then \
		   $(ECHO) -e "passed\t$${repo}\t$${i}" >> $(VERIFY_LOG);  \
                else \
		   $(ECHO) -e "failed\t$${repo}\t$${i}" >> $(VERIFY_LOG);  \
                fi \
	done                                \
	done
	sort -r $(VERIFY_LOG) >  /tmp/check.$$$$ ; cp  /tmp/check.$$$$   $(VERIFY_LOG)

BUILD_LOG=build.log

pkg:
	rm -f $(PROGRESS_LOG)
	@for repo in ${REPOS};                   \
	do                                      \
	for i in `ls product/build/base_os/source/repo/$${repo}`;             \
	do                                  \
		$(ECHO) -e "start\t$${repo}\t$${i}" >> $(BUILD_LOG);  \
		if docker run -i -t -v "$(PWD)/tool/apk:/var/local/packages" -v "$(PWD)/tool/pki:/pki"  -v $(PWD)/product/build/base_os/source/repo:/aports  -v $(PWD)/tool/builder:/root $(TOOLS_IMAGE)   make -C /root check ARCH=${ARCH} PACKAGE=$${i} REPO=$${repo} ; then \
		   docker run -i -t -v "$(PWD)/tool/apk:/var/local/packages" -v "$(PWD)/tool/pki:/pki"  -v $(PWD)/product/build/base_os/source/repo:/aports  -v $(PWD)/tool/builder:/root $(TOOLS_IMAGE)   make -C /root build ARCH=${ARCH} PACKAGE=$${i} REPO=$${repo} ; \
		   tm=`date +"%s"`; \
		   $(ECHO) -e "$$tm\tstop\tOK" >> $(BUILD_LOG);  \
                else \
		   tm=`date +"%s"`; \
		   $(ECHO) -e "$$tm\tstop\tError" >> $(BUILD_LOG);  \
                fi \
	done                                \
	done

keygen:
	mkdir -p tool/pki 
	openssl genrsa -out tool/pki/iafw.rsa 1024
	openssl rsa -in tool/pki/iafw.rsa -pubout > tool/pki/iafw.rsa.pub
	chmod 755 -R tool/pki

sign:
	@for repo in ${REPOS};                   \
	do                                      \
	   docker run -i -t -v "$(PWD)/tool/apk:/var/local/packages" -v "$(PWD)/tool/pki:/pki"  -v $(PWD)/product/build/base_os/source/repo:/aports  -v $(PWD)/tool/builder:/root   $(TOOLS_IMAGE)  make -C /root index ARCH=${ARCH}  REPO=$${repo} ; \
	   docker run -i -t -v "$(PWD)/tool/apk:/var/local/packages" -v "$(PWD)/tool/pki:/pki"  -v $(PWD)/product/build/base_os/source/repo:/aports  -v $(PWD)/tool/builder:/root  $(TOOLS_IMAGE)   make -C /root sign  ARCH=${ARCH}  REPO=$${repo} ; \
	done

TEST_MAKEFILE = $(DIR)/test/Makefile
.PHONY: $(TEST_MAKEFILE)
$(TEST_MAKEFILE) :
	mkdir -p  $(DIR)/test
	echo "" > $@
	echo "# Generated by $(BASE_OS_IMAGE)" >> $@
	echo "" >> $@
	echo "# This is a simple test that lists all packages being resolved by Alpine package manager" >> $@
	echo "# The output is included in the aggregated SBOM " >> $@
	echo "" >> $@
	echo "include ../build/base_os/config/settings" >> $@
	echo "" >> $@
	echo "CONTAINER_IMAGE = \$$(BASE_OS_IMAGE):\$$(BASE_OS_VERSION)" >> $@
	echo "" >> $@
	echo "test:" >> $@
	echo "\tdocker run   --rm  -i --entrypoint='/usr/local/bin/bom.sh'  --name alpine\$$(ALPINE_VERSION) \$$(CONTAINER_IMAGE) | tee os.bom" >> $@
	echo "sh:" >> $@
	echo "\tdocker run   --rm  -it  --name alpine\$$(ALPINE_VERSION) \$$(CONTAINER_IMAGE) sh" >> $@


BUILDER_MAKEFILE = tool/builder/Makefile
.PHONY: $(BUILDER_MAKEFILE)
$(BUILDER_MAKEFILE) :
	mkdir -p  tool/builder
	echo "" > $@
	echo "# Generated by, do not edit"  >> $@
	echo "" >> $@
	echo "BUILD_DIR=/var/local/aports" >> $@
	echo "REPODEST=/var/local/packages" >> $@
	echo "ABUILD=abuild -F -P \$$(REPODEST)" >> $@
	echo "" >> $@
	echo "ARCH=x86_64" >> $@
	echo "PACKAGE=zlib" >> $@
	echo "REPO=main" >> $@
	echo "" >> $@
	echo "prepare:" >> $@
	echo "\t@mkdir -p \$$(BUILD_DIR)/\$$(REPO)/\$$(PACKAGE)" >> $@
	echo "\t@cp -r /aports/\$$(REPO)/\$$(PACKAGE)/*  \$$(BUILD_DIR)/\$$(REPO)/\$$(PACKAGE)" >> $@
	echo "\t@echo 'PACKAGER_PRIVKEY="/pki/iafw.rsa"' > /etc/abuild.conf" >> $@
	echo "\t@rm -f \$$(REPODEST)/\$$(REPO)/\$$(ARCH)/APKINDEX.tar.gz" >> $@
	echo "" >> $@
	echo "fetch:" >> $@
	echo "\t@( cd \$$(BUILD_DIR)/\$$(REPO)/\$$(PACKAGE) && \$$(ABUILD) fetch )" >> $@
	echo "" >> $@
	echo "verify: fetch" >> $@
	echo "\t@( cd \$$(BUILD_DIR)/\$$(REPO)/\$$(PACKAGE) && \$$(ABUILD) sanitycheck )" >> $@
	echo "\t@( cd \$$(BUILD_DIR)/\$$(REPO)/\$$(PACKAGE) && \$$(ABUILD) verify )" >> $@
	echo "" >> $@
	echo "unpack: " >> $@
	echo "\t@( cd \$$(BUILD_DIR)/\$$(REPO)/\$$(PACKAGE) && \$$(ABUILD) unpack )" >> $@
	echo "" >> $@
	echo "patch: " >> $@
	echo "\t@( cd \$$(BUILD_DIR)/\$$(REPO)/\$$(PACKAGE) && \$$(ABUILD) prepare )" >> $@
	echo "" >> $@
	echo "deps: " >> $@
	echo "\t@( cd \$$(BUILD_DIR)/\$$(REPO)/\$$(PACKAGE) && \$$(ABUILD) deps )" >> $@
	echo "" >> $@
	echo "abuild: " >> $@
	echo "\t@( cd \$$(BUILD_DIR)/\$$(REPO)/\$$(PACKAGE) && \$$(ABUILD)  )" >> $@
	echo "\t@rm -f \$$(REPODEST)/\$$(REPO)/\$$(ARCH)/APKINDEX.tar.gz" >> $@
	echo "index: " >> $@
	echo "\t@( cd \$$(REPODEST)/\$$(REPO)/\$$(ARCH)  && rm -f  APKINDEX.unsigned.tar.gz  )" >> $@
	echo "\t@( cd \$$(REPODEST)/\$$(REPO)/\$$(ARCH)  && apk index -o APKINDEX.tar.gz *.apk  )" >> $@
	echo "" >> $@
	echo "sign: " >> $@
	echo "\t@( cd \$$(REPODEST)/\$$(REPO)/\$$(ARCH)  && abuild-sign -k /pki/iafw.rsa APKINDEX.tar.gz  )" >> $@
	echo "" >> $@
	echo "build: prepare verify unpack patch abuild" >> $@
	echo "" >> $@
	echo "check: prepare verify" >> $@
	echo "" >> $@



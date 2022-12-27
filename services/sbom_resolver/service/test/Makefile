

CLIENT_ID=product
CLIENT_SECRET=qwerty

TOKEN_URL=http://localhost:8080/resolver/alpine/v1
TOKEN_URL=https://lb.t2data.com/resolver/alpine/v1
TOKEN_URL=https://lb.t2data.com/token/v1
#TOKEN_URL=https://compliance-cicd.internal.ericsson.com/token/v2

URL=http://localhost:8080
URL=https://lb.t2data.com

TOOLS_REPO      = docker.io/bomres
ALPINE_BUILDER  = base_os_alpine:latest
BASE_OS_IMAGE   = $(TOOLS_REPO)/$(ALPINE_BUILDER)

include ../build/config/settings
#CONTAINER_IMAGE = $(TOOLS_REPO)/$(SERVICE_IMAGE):$(SERVICE_VERSION)
CONTAINER_IMAGE = $(SERVICE_IMAGE):$(SERVICE_VERSION)

save: 
	mkdir -p $(DIR)/tools/images
	rm -f $(DIR)/tools/images/$(ALPINE_BUILDER).tar 
	docker save $(BASE_OS_IMAGE) > $(DIR)/tools/images/$(ALPINE_BUILDER).tar 

load: 
	docker load <  $(DIR)/tools/images/$(ALPINE_BUILDER).tar 


DIR=alpine

CURL=curl --silent -k --trace-ascii /tmp/log  --fail --show-error --http1.1  -L


JWT = $(shell cat access_token)
ID = $(shell cat uuid) 

token:
	@$(CURL)  -d "scope=s1 s2" --data "grant_type=client_credentials&client_id=$(CLIENT_ID)&client_secret=$(CLIENT_SECRET)"  \
        $(TOKEN_URL)/token  | grep access_token  | awk -F\" '{print $$4}' >  access_token


token_mtls:
	@openssl x509 -noout -modulus -in cert.pem | openssl md5
	@openssl rsa -noout -modulus -in priv.pem | openssl md5
	@$(CURL)   --cert cert.pem --key priv.pem  --data "grant_type=client_credentials&client_id=$(CLIENT_ID)&client_secret=$(CLIENT_SECRET)"  \
	$(TOKEN_URL)/token  | grep access_token  | awk -F\" '{print $$4}' >  access_token


dump:
	@cat access_token   |  awk -F. '{print $$2}' |  base64 -d 2> /dev/null | jq '.' 



# Retrieve file 
rest_retrieve:
	@$(CURL) -X POST   "$(URL)/resolver/alpine/v1/file"                         \
                -H  "Authorization: Bearer $(JWT)"                                  \
		-H  "Content-Type: application/json"                                \
		--data '{ "commit": "273f76be99", "path": "main/libcap-ng/apply-disable.patch", "repository_id": "bf08e96b-da14-4355-9024-ea6ceb937d60" }' | tee  file.c 


# List repos  by uuid
list:
	@$(CURL)    "$(URL)/resolver/alpine/v1/src"  \
                -H  "Authorization: Bearer $(JWT)" \
                -H  "accept: application/json" | tee dump.json  | jq -r '.[0].uuid' > uuid  && cat dump.json


# Delete repository by uuid
del:
	@$(CURL)   -X DELETE   "$(URL)/resolver/alpine/v1/src/$(ID)"  \
                -H  "Authorization: Bearer $(JWT)" \
                -H  "accept: application/json"



ENDPOINT=bom/v1/aggregate
ENDPOINT=resolver/alpine/v1/aggregate


rest_aggregate: 
	@echo "Posting data for aggregation to $(URL)/$(ENDPOINT)"
	@$(CURL)  -X POST   -s -o - "$(URL)/$(ENDPOINT)"                                        \
                -H  "accept: application/json"                                                     \
                -H  "Authorization: Bearer $(JWT)"                                                 \
                -H  "Content-Type: multipart/form-data"                                            \
                -F "config=@$(PWD)/$(DIR)/build/base_os/config/settings;type=application/txt"                                    \
                -F "desired=@$(PWD)/$(DIR)/build/base_os/sbom/os.conf;type=application/txt"                                    \
                -F "pkgindex=@$(PWD)/$(DIR)/build/base_os/sbom/apkindex.tar;type=application/x-tar"                            \
                -F "resolved=@$(PWD)/$(DIR)/build/base_os/sbom/os.bom;type=application/txt"  | tee $(PWD)/$(DIR)/build/base_os/sbom/aggregated.json


container_aggregate: 
	@docker run   --rm -it $(OPTIONS)  -v "$$PWD/$(DIR)/build:/sandbox"  -e IMAGE=$(BASE_OS_IMAGE) $(BASE_OS_IMAGE)  aggregate

python_aggregate:
	python3  ../build/bomres/bomres/lib/aggregate_bom.py  --pkgindex $(PWD)/$(DIR)/build/base_os/sbom/apkindex.tar    --desired $(PWD)/$(DIR)/build/base_os/sbom/os.conf  \
                          --resolved $(PWD)/$(DIR)/build/base_os/sbom/os.bom  --config $(PWD)/$(DIR)/build/base_os/config/settings  --output $(PWD)/$(DIR)/build/base_os/sbom/aggregated.json #  --debug


#  Debug and test 
#  Use the container to generate metadata , debug python code outside containers 
#  
#  All changes in python must be installed with pip to take effect 
#
#  mkdir -p /tmp/sandbox 
#  cd /tmp/sandbox 
#  docker run -it --rm docker.io/bomres/base_os_alpine make > Makefile
#  make config
#  make resolve 
#
pip: 
	( cd ../build/bomres  && pip3 install . )

SANDBOX=/tmp/sandbox
ind_0: 
	rm -f  $(PWD)/$(DIR)/build/base_os/sbom/index.json 
	python3  ../build/bomres/bomres/lib/aggregate_bom.py      --pkgindex $(SANDBOX)/product/build/base_os/sbom/apkindex.tar   --output   $(SANDBOX)/product/build/base_os/sbom/index.json

ind_1: 
	python3  ../build/bomres/bomres/lib/create_apkcache.py    --apkindex $(SANDBOX)/product/build/base_os/sbom/index.json     --src      /tmp/alpine/src        --checkout   /tmp/alpine/checkout --cache /tmp/alpine/cache --debug # --deep

ind_2: 
	python3  ../build/bomres/bomres/lib/parse_apkbuild.py     --apkindex $(SANDBOX)/product/build/base_os/sbom/index.json     --checkout /tmp/alpine/checkout   --cache      /tmp/alpine/cache

res_0: 
	python3  ../build/bomres/bomres/lib/resolve_bom.py   --packages $(SANDBOX)/product/build/base_os/sbom/aggregated.json    --cache /tmp/alpine/cache         --output $(SANDBOX)/product/build/base_os/sbom/resolved.json #  --debug 


python_index: 
	# Extract information from all APKINDEX.tar.gz used in the binary build , output  is index.json 
	python3  ../build/bomres/bomres/lib/aggregate_bom.py      --pkgindex $(PWD)/$(DIR)/build/base_os/sbom/apkindex.tar   --output   $(PWD)/$(DIR)/build/base_os/sbom/index.json

	# Checkout anc copy internal code, patches and APKBUILD from aports repository , directory structure in  /tmp/alpine/checkout 
        # Each repo tag is retrieved from index.json 
	python3  ../build/bomres/bomres/lib/create_apkcache.py    --apkindex $(PWD)/$(DIR)/build/base_os/sbom/index.json     --src      /tmp/alpine/src        --checkout   /tmp/alpine/checkout --cache /tmp/alpine/cache --debug # --deep

        # Create /tmp/alpine/cache/APKINDEX-aa847b1b1602c1d767b7c58a148ff93c.json based on index.json and metadata from parsed aports data 
	python3  ../build/bomres/bomres/lib/parse_apkbuild.py     --apkindex $(PWD)/$(DIR)/build/base_os/sbom/index.json     --checkout /tmp/alpine/checkout   --cache      /tmp/alpine/cache


python_resolve: 
	python3  ../build/bomres/bomres/lib/resolve_bom.py   --packages $(PWD)/$(DIR)/build/base_os/sbom/aggregated.json    --cache /tmp/alpine/cache         --output $(PWD)/$(DIR)/build/base_os/sbom/resolved.json #  --debug 


python_file: 
	python3 ../build/bomres/bomres/lib/get_file_git.py  --src /tmp/alpine/src --resolved  $(PWD)/$(DIR)/build/base_os/sbom/resolved.json   --output $(PWD)/$(DIR)/build/base_os/source  --mode internal --type patch  --debug
	python3 ../build/bomres/bomres/lib/get_file_git.py  --src /tmp/alpine/src --resolved  $(PWD)/$(DIR)/build/base_os/sbom/resolved.json   --output $(PWD)/$(DIR)/build/base_os/source  --mode internal --type code  --debug
	python3 ../build/bomres/bomres/lib/get_file_git.py  --src /tmp/alpine/src --resolved  $(PWD)/$(DIR)/build/base_os/sbom/resolved.json   --output $(PWD)/$(DIR)/build/base_os/source  --mode internal --type build  --debug

	python3 ../build/bomres/bomres/lib/get_file_git.py  --src /tmp/alpine/src --resolved  $(PWD)/$(DIR)/build/base_os/sbom/resolved.json   --output $(PWD)/$(DIR)/build/base_os/source  --mode external --type code  --debug
	python3 ../build/bomres/bomres/lib/get_file_git.py  --src /tmp/alpine/src --resolved  $(PWD)/$(DIR)/build/base_os/sbom/resolved.json   --output $(PWD)/$(DIR)/build/base_os/source  --mode external --type patch  --debug



ptool: 
	python3 ../build/bomres/bomres/lib/resolve_tool.py   --resolved  $(PWD)/$(DIR)/build/base_os/sbom/resolved.json  --packages
	#python3 ../build/bomres/bomres/lib/resolve_tool.py   --resolved  $(PWD)/$(DIR)/build/base_os/sbom/resolved.json  --settings

pctool: 
	docker run -i -t -v "$$PWD/$(DIR)/build/base_os/sbom:/sbom"   $(CONTAINER_IMAGE) tool

config:
	@docker run   --rm -it $(OPTIONS)  -v "$$PWD/$(DIR)/build:/sandbox" -w /sandbox  -e IMAGE=$(BASE_OS_IMAGE) $(BASE_OS_IMAGE)  config

init:
	@docker run   --rm -it $(OPTIONS)  -v "$$PWD/$(DIR)/build:/sandbox" -w /sandbox  -e IMAGE=$(BASE_OS_IMAGE) $(BASE_OS_IMAGE)  init


prepare:
	@make -C $$PWD/$(DIR)/build/base_os  builder

public_build:
	@make -C $$PWD/$(DIR)/build/base_os  public_build

private_build:
	@make -C $$PWD/$(DIR)/build/base_os  private_build

download:
	@make -C  $$PWD/$(DIR)/build/base_os  download

test: 
	@make -C $$PWD/$(DIR)/test  test DIR=$(DIR)
	cp -f    $$PWD/$(DIR)/test/os.bom $$PWD/$(DIR)/build/base_os/sbom/os.bom

syft: 
	@make -C $$PWD/$(DIR)/test  syft DIR=$(DIR)

shell: 
	@make -C $$PWD/$(DIR)/test  sh DIR=$(DIR)

clean: 
	rm -rf $(DIR) 
	rm -rf /tmp/alpine/cache/*
	rm -rf /tmp/alpine/checkout/*



# Initial clone of git repo inito service
rest_clone:
	@$(CURL) --max-time 400  -X POST "$(URL)/resolver/alpine/v1/src" \
                -H  "Authorization: Bearer $(JWT)" \
                -H 'Content-Type: multipart/form-data' \
                -F "url=https://git.alpinelinux.org/aports" |  tee dump.json  | jq -r '.[0].uuid' > uuid  && cat dump.json

rest_index:
	@echo "Posting apkindex.tar to  $(URL)/resolver/alpine/v1/index "
	@$(CURL)  -X POST   -s -o - -X POST "$(URL)/resolver/alpine/v1/index" \
                -H  "Authorization: Bearer $(JWT)" \
                -H 'Content-Type: multipart/form-data' \
                -F apkindex=@$(DIR)/build/base_os/sbom/apkindex.tar  | tee  $(DIR)/build/base_os/sbom/index.json


rest_resolve:
	@echo "Posting aggregated SBOM to resolver  $(URL)/resolver/alpine/v1/resolve"
	@$(CURL) -X POST "$(URL)/resolver/alpine/v1/resolve" \
                -H  "Authorization: Bearer $(JWT)" \
                -H  "X-Message-Ttl: 10"                                    \
                -H 'Content-Type: multipart/form-data' \
                -F sbom=@$(DIR)/build/base_os/sbom/aggregated.json | tee $(DIR)/build/base_os/sbom/resolved.json



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


base_os_config: config $(DIR)/test/Makefile
base_os: base_os_config init  prepare public_build download private_build test 

hans: public_build download private_build test container_aggregate python_index python_resolve

test_cycle: clean base_os container_aggregate python_index python_resolve 

tool: index resolve 

service: token rest_index rest_resolve retrieve_patches


view:
	vi $(DIR)/build/base_os/config/settings
	vi $(DIR)/build/base_os/config/packages
	vi $(DIR)/build/base_os/sbom/resolved.json
	tree $(DIR)/build/base_os/source


#
# Generate test file so we can clean alpine product directory 


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











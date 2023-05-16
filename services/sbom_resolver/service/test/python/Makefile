#################################################   
#
#  Test of BomResolver from Python 
#
#  Note: $ make pip must be executed prior to test, due to dependencies 
#
#################################################   


# Sandbox for image build 
SANDBOX=/home/hans/bomres/sandbox
TARGET=tool
TARGET=product

# Cloned repositoy of Alpine Build Manifest ( APKBUILD ) 
ALPINE_REPO=/tmp/alpine
ALPINE_REPO=/home/hans/bomres/alpine

# To avoid problems , always run pip install when python source is changed , see cycle rule 
pip: 
	( cd ../../build/bomres  && pip3 install . )

# In $(TARGET)ion , the Alpine reposity should be mirrored and indexed in advance 
#                 Alpine source should be cloned to reduce network traffic and avoid rate limiting in github/gitlab 


#################################################   
#
# aggregated.json extracts data from the binary build 
# input is: 
#     apkindex.tar: 
#           alpine/v3.16/main/x86_64/APKINDEX.tar.gz
#           alpine/v3.16/community/x86_64/APKINDEX.tar.gz
#     os.conf   "Desired" list of packages
#     os.bom    "Resolved" list of packages with all transitive package depencies 
#     settings  Specify location of package repositories, architecture, version of Alpine 
#
#################################################   

aggregate:
	python3  ../../build/bomres/bomres/lib/aggregate_bom.py  --pkgindex $(SANDBOX)/$(TARGET)/build/base_os/sbom/apkindex.tar    --desired $(SANDBOX)/$(TARGET)/build/base_os/sbom/os.conf  \
                          --resolved $(SANDBOX)/$(TARGET)/build/base_os/sbom/os.bom  --config $(SANDBOX)/$(TARGET)/build/base_os/config/settings  --output $(SANDBOX)/$(TARGET)/build/base_os/sbom/aggregated.json #  --debug


#################################################   
#
# indexing extract metadata from Alpine build manifests by matching metadata found in APKINDEX.tar.gz 
# The result is written to $(ALPINE_REPO)/cache/APKINDEX-<hash from build>.json 
# The process is divided in three stages 
# 1. pkindex.tar -> index.json 
# 2. index.json and $(ALPINE_REPO)/src -> $(ALPINE_REPO)/checkout  , one entry for each APKBUILD , the cache argument is just passed to prevent duplication of data 
# 3. index.json  and $(ALPINE_REPO)/checkout  ->  $(ALPINE_REPO)/cache/APKINDEX-ad999d5941023eea1e8ecd0dbd2d8a71.json
#
# The dataflow is designed to scale when deployed in Kubernetes 
#  $(ALPINE_REPO)/cache is shared among all pods 
#  $(ALPINE_REPO)/checkout is  local for each pod 
#  $(ALPINE_REPO)/src is  local for each pod and created by the init container 
#
#################################################   

python_index: ind_0 ind_1 ind_2 

ind_0: 
	rm -f  $(SANDBOX)/$(TARGET)/build/base_os/sbom/index.json 
	python3  ../../build/bomres/bomres/lib/aggregate_bom.py      --pkgindex $(SANDBOX)/$(TARGET)/build/base_os/sbom/apkindex.tar   --output   $(SANDBOX)/$(TARGET)/build/base_os/sbom/index.json

ind_1: 
	python3  ../../build/bomres/bomres/lib/create_apkcache.py    --apkindex $(SANDBOX)/$(TARGET)/build/base_os/sbom/index.json     --src      $(ALPINE_REPO)/src        --checkout   $(ALPINE_REPO)/checkout --cache $(ALPINE_REPO)/cache --debug  # --deep

ind_2: 
	python3  ../../build/bomres/bomres/lib/parse_apkbuild.py     --apkindex $(SANDBOX)/$(TARGET)/build/base_os/sbom/index.json     --checkout $(ALPINE_REPO)/checkout   --cache      $(ALPINE_REPO)/cache



#################################################   
#
# The resolver stage connects metadata extracted during build with metadata extracted source build manifests ( APKBUILD ) 
#  aggregated.json  and  $(ALPINE_REPO)/cache/APKINDEX-ad999d5941023eea1e8ecd0dbd2d8a71.json -> resolved.json 
#
#################################################   

python_resolve: 
	python3  ../../build/bomres/bomres/lib/resolve_bom.py   --packages $(SANDBOX)/$(TARGET)/build/base_os/sbom/aggregated.json    --cache $(ALPINE_REPO)/cache         --output $(SANDBOX)/$(TARGET)/build/base_os/sbom/resolved.json   --debug 



#################################################   
#
# resolved.json is input to retrieve ALL source required to build the code  according to the "Aggregator model" 
# internal 
#   code 
#   patches 
#   build manifest ( APKBUILD ) 
# external 
#   code 
#   patches 
#
#################################################   

python_file: src_dir  ip ic ib ec ep 

src_dir:
	rm -rf   $(SANDBOX)/$(TARGET)/build/base_os/source
	mkdir -p $(SANDBOX)/$(TARGET)/build/base_os/source
ip: 
	python3 ../../build/bomres/bomres/lib/get_file_git.py  --src $(ALPINE_REPO)/src --resolved  $(SANDBOX)/$(TARGET)/build/base_os/sbom/resolved.json   --output $(SANDBOX)/$(TARGET)/build/base_os/source  --mode internal --type patch  --debug
ic: 
	python3 ../../build/bomres/bomres/lib/get_file_git.py  --src $(ALPINE_REPO)/src --resolved  $(SANDBOX)/$(TARGET)/build/base_os/sbom/resolved.json   --output $(SANDBOX)/$(TARGET)/build/base_os/source  --mode internal --type code  --debug
ib: 
	python3 ../../build/bomres/bomres/lib/get_file_git.py  --src $(ALPINE_REPO)/src --resolved  $(SANDBOX)/$(TARGET)/build/base_os/sbom/resolved.json   --output $(SANDBOX)/$(TARGET)/build/base_os/source  --mode internal --type build  --debug

ec: 
	python3 ../../build/bomres/bomres/lib/get_file_git.py  --src $(ALPINE_REPO)/src --resolved  $(SANDBOX)/$(TARGET)/build/base_os/sbom/resolved.json   --output $(SANDBOX)/$(TARGET)/build/base_os/source  --mode external --type code  --debug
ep: 
	python3 ../../build/bomres/bomres/lib/get_file_git.py  --src $(ALPINE_REPO)/src --resolved  $(SANDBOX)/$(TARGET)/build/base_os/sbom/resolved.json   --output $(SANDBOX)/$(TARGET)/build/base_os/source  --mode external --type patch  --debug



#################################################   
#
# The "Desired" SBOM for the tool is autogenerated from the $(TARGET) resolved sbom 
#
#################################################   

packages: 
	python3 ../../build/bomres/bomres/lib/resolve_tool.py   --resolved  $(SANDBOX)/$(TARGET)/build/base_os/sbom/resolved.json  --packages

settings: 
	python3 ../../build/bomres/bomres/lib/resolve_tool.py   --resolved  $(SANDBOX)/$(TARGET)/build/base_os/sbom/resolved.json  --settings


cycle: pip aggregate python_index python_resolve python_file 



#################################################   
#
# apklib extracts data from APKBUILD manifest 
#
#################################################   

PACKAGE=gcc
apklib: 
	python3 ../../build/bomres/bomres/lib/apklib.py --checkout $(ALPINE_REPO)/checkout/ --src $(ALPINE_REPO)/src/  --name  $(PACKAGE) --apkindex $(SANDBOX)/$(TARGET)/build/base_os/sbom/index.json    --output /tmp/apklib.json


#################################################   
#
# Useful for demo of the datadriven design 
#
#################################################   
view:
	vi $(SANDBOX)/$(TARGET)/build/base_os/config/settings
	vi $(SANDBOX)/$(TARGET)/build/base_os/config/packages
	vi $(SANDBOX)/$(TARGET)/build/base_os/sbom/resolved.json
	tree $(SANDBOX)/$(TARGET)/build/base_os/source



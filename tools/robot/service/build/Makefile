include ../../base_os/build/base_os/config/settings
include config/settings

BASE_OS=$(BASE_OS_IMAGE):$(BASE_OS_VERSION) 
CONTAINER_IMAGE = $(SERVICE_IMAGE):$(SERVICE_VERSION)


build:
	docker build -t  $(CONTAINER_IMAGE) --build-arg IMAGE=$(BASE_OS)  -f Containerfile .

pip: 
	pip3 install --no-cache-dir -r requirements.txt



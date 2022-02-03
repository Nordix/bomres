include ../../base_os/build/base_os/config/settings
include config/settings

BASE_OS=$(BASE_OS_IMAGE):$(BASE_OS_VERSION) 
CONTAINER_IMAGE = $(SERVICE_IMAGE):$(SERVICE_VERSION)

mock:
	connexion run service/openapi.yaml --stub --debug

build:
	docker build -t  $(CONTAINER_IMAGE) --build-arg IMAGE=$(BASE_OS)  -f Containerfile .


OPTIONS=  -v  /tmp/alpine/src:/mnt/alpine/src
OPTIONS+= -v  /tmp/alpine/checkout:/mnt/alpine/checkout
OPTIONS+= -v  /tmp/alpine/cache:/mnt/alpine/cache

OPTIONS+= -e  APORTS_SRC=/mnt/alpine/src
OPTIONS+= -e  APORTS_CHECKOUT=/mnt/alpine/checkout
OPTIONS+= -e  APORTS_CACHE=/mnt/alpine/cache

OPTIONS+= -p  8080:8080

python:
	@mkdir -p /tmp/alpine/src
	@mkdir -p /tmp/alpine/checkout
	@mkdir -p /tmp/alpine/cache
	python3 app.py

run:
	docker run -i -t  $(OPTIONS)  $(CONTAINER_IMAGE) server
sh:
	docker run -i -t  $(OPTIONS)  $(CONTAINER_IMAGE) sh

clean: 
	@rm -f *.pem *.jwk


pep:
	pip3 install autopep8
	autopep8 --in-place  cache.py 

keygen:
	openssl genrsa -out priv.pem 1024
	openssl rsa -in priv.pem -pubout > pub.pem



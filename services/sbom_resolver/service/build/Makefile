include ../../middleware/build/config/settings

include config/settings


MW_IMAGE=$(MIDDLEWARE_IMAGE):$(MIDDLEWARE_VERSION)


CONTAINER_IMAGE = $(SERVICE_IMAGE):$(SERVICE_VERSION)


mock:
	connexion run openapi.yaml --stub --debug


build:
	docker build -t  $(CONTAINER_IMAGE) --build-arg MW_IMAGE=$(MW_IMAGE)  -f Containerfile .



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

clean: 
	@rm -f *.pem *.jwk


pep:
	pip3 install autopep8
	autopep8 --in-place  cache.py 

keygen:
	openssl genrsa -out priv.pem 1024
	openssl rsa -in priv.pem -pubout > pub.pem


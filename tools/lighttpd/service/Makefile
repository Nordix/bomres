include ../base/product/build/base_os/config/settings

include  config/settings


CONTAINER_IMAGE = $(SERVICE_IMAGE):$(SERVICE_VERSION)


build:
	mkdir -p alpine 
	cp *.css alpine 
	cp -r /opt/sandbox/product/build/base_os/download/alpine/*  alpine
	docker build -t  $(CONTAINER_IMAGE) --build-arg BASE_OS_IMAGE=$(BASE_OS_IMAGE):$(BASE_OS_VERSION)  -f Containerfile .
	rm -rf  alpine

OPTIONS = -p  8080:8080
OPTIONS += -e PORT=8080
OPTIONS += -e SERVER_ROOT=/alpine
OPTIONS += -e USER=lighttpd  
OPTIONS += -e SERVER_NAME="http://localhost:8080/alpine/public"
OPTIONS += -e MAX_FDS=16384 

#


run:
	docker run -i -t  $(OPTIONS)  $(CONTAINER_IMAGE) server
sh:
	docker run -i -t  $(OPTIONS)  $(CONTAINER_IMAGE) sh 


local:
	( cd hugo && hugo server  -verbose --config config.yaml  --port 8080  --bind="0.0.0.0" --baseURL="http://localhost:8080/hugo" public ) 


clean: 
	rm -rf hugo/public 

PORT=8080
SERVER_ROOT=$(PWD)/kanban
SERVER_ROOT=/home/hans/development/git-clones/kanban/frontend/build
SERVER_DIR_ROOT=/opt/sandbox/product/build/base_os/download/alpine/
SERVER_NAME="http://localhost:$(PORT)/alpine/public" 

light:
	export SERVER_ROOT=$(SERVER_ROOT)  && export PORT=$(PORT) && export SERVER_NAME=$(SERVER_NAME) && export MAX_FDS=16384 && /usr/sbin/lighttpd  -D -f  lighttpd.conf 
dirlight:
	export SERVER_ROOT=$(SERVER_DIR_ROOT)  && export PORT=$(PORT) && export SERVER_NAME=$(SERVER_NAME) && export MAX_FDS=16384 && /usr/sbin/lighttpd  -D -f  lighttpd_dir.conf 

p: 
	export SERVER_ROOT=$(SERVER_ROOT)  && export PORT=$(PORT) && export SERVER_NAME=$(SERVER_NAME) && export MAX_FDS=16384 && /usr/sbin/lighttpd  -f  lighttpd.conf -p 


FILE=style.css
FILE=favicon.ico
FILE=index.html
FILE=static/js/2.3d127216.chunk.js

curl: 
	curl  --verbose --http1.1  \
		--header 'Host: localhost:8080' \
		--header 'User-Agent: Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/109.0' \
		--header 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8' \
		--header 'Accept-Language: en-US,en;q=0.5' \
		--header 'Accept-Encoding: gzip, deflate, br' \
		--header 'Connection: keep-alive' \
		--header 'Upgrade-Insecure-Requests: 1' \
		--header 'Sec-Fetch-Dest: document' \
		--header 'Sec-Fetch-Mode: navigate' \
		--header 'Sec-Fetch-Site: none' \
		--header 'Sec-Fetch-User: ?1' \
		http://localhost:3000/kanban/$(FILE) # -o $(FILE) 


#### Build native 
# apt install liblua5.3-dev libsqlite3-dev sqlite3-dev libldap-dev libdbi-dev  
# tar xvzf lighttpd-1.4.67.tar.gz
# Check configure rule in Alpine 3.17  
# ./configure --prefix=/usr --disable-dependency-tracking --enable-lfs 
# --libdir=/usr/lib/lighttpd --without-mysql --without-attr 
# --with-webdav-props --with-webdav-locks --without-gdbm --with-pcre2 --with-dbi --with-ldap --with-openssl --with-zstd --with-brotli --with-lua

# /usr/sbin/lighttpd -v
# lighttpd/1.4.67 (ssl) - a light and fast webserver

# - 1.4.65 - 2022-06-07
# [multiple] WebSockets over HTTP/2 (fixes #3151)  
#
#
#
# Deploy to docker.io 
#
#
REGISTRY ?= docker.io
REPOSITORY ?= bomres


tag:
	podman tag $(CONTAINER_IMAGE) $(REGISTRY)/$(REPOSITORY)/$(CONTAINER_IMAGE)

login:
	podman login $(REGISTRY)

push:
	podman push $(REGISTRY)/$(REPOSITORY)/$(CONTAINER_IMAGE)







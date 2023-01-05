#
# Work in progress , dont expect this to work 
#

CLIENT_ID=product
CLIENT_SECRET=qwerty

TOKEN_URL=http://localhost:8080/resolver/alpine/v1



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




service: token rest_index rest_resolve retrieve_patches











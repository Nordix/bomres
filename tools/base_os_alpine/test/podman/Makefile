#
# https://github.com/jonasbb/podman-gitlab-runner 
# https://www.redhat.com/sysadmin/podman-inside-container
#
#
CWD := $(shell cd -P -- '$(shell dirname -- "$0")' && pwd -P)
build: 
	podman build -f Containerfile -t podinpod . 

run: 
	mkdir -p data
	mkdir -p /tmp/alpine
	podman run -i -t --privileged -v$(CWD)/data:/data -v/tmp/alpine:/tmp/alpine  podinpod sh 

clean: 
	rm -rf data 

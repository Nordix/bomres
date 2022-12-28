#
# https://github.com/jonasbb/podman-gitlab-runner 
# https://www.redhat.com/sysadmin/podman-inside-container
#
build: 
	podman build -f Containerfile -t podinpod . 

run: 
	mkdir -p data
	podman run -i -t --privileged -v./data:/data  podinpod sh 

clean: 
	rm -rf data 

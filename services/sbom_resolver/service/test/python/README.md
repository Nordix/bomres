

# Overview 
Before deep dive into the internals, lets get an overview of the setup. 

## prepare sandbox  
Start within a clean directory and execute make for the base_os_alpine container. 


```
$ mkdir -p /opt/sandbox
$ cd /opt/sandbox 
$ podman run  --rm docker.io/bomres/base_os_alpine make > Makefile

```
The make command  is passed as a parameter to /docker-entrypoint.sh inside the 
base_os_alpine container.  Below is the code snippet that copies the Makkefile 
to standard out. 
NOTE: avoid use of -t argument since it may add newlines. 

```

#!/bin/sh                                                                                    
if [ "$1" = 'make' ]; then                                                                                 
    cat /opt/base_os/templates/makefiles/Makefile.bootstrap 
fi 
```
 

## make config
The product to be built requires tools, therefore there is two rules that operates 
in different directories.
The product resides in $(DIR)/product and tools in $(DIR)/tool. The steps are basicly the same, it is only the 
directories that differs. 

[podman](https://www.redhat.com/sysadmin/podman-inside-container) may need some configuration. 

The first command in the _config: rule creates the build directory. The subdirectories are created from inside the 
container by mount the host with the container using -v flag. This step may fail if you have missining capabilities. 

```
$HOME/.config/containers/containers.conf  med innehållet:default_capabilities = [
     "AUDIT_WRITE",
     "CHOWN",
     "DAC_OVERRIDE",
     "FOWNER",
     "FSETID",
     "KILL",
     "MKNOD",
     "NET_BIND_SERVICE",
     "NET_RAW",
     "SETGID",
     "SETPCAP",
     "SETUID",
     "SYS_CHROOT",
]
```

```
DIR ?= $(CWD)

config:
         @make _config DIR=$(DIR)/product
	
tool_config:
        @mkdir -p $(DIR)/tool/build/base_os/config/

_config:

        @mkdir -p $(DIR)/build^
        @podman run   --rm  $(OPTIONS)  -v "$(DIR)/build:/sandbox" -w /sandbox  -e IMAGE=$(BASE_OS_IMAGE) $(BASE_OS_IMAGE)  config
```

## make build

This single target calls several targets 

- init 
- config 
- prepare 
- public_build 
- download 
- private_build 
- test 
- aggregate

For now just a subset are covered in this guide
### init 

```
    if test ! -f /sandbox/base_os/build_dir ; then                                                           
       mkdir -p /sandbox/base_os/build_dir/scripts                                                           
       cp -f /opt/base_os/scripts/apk-install  /sandbox/base_os/build_dir/scripts/apk-install                
       cp -f /opt/base_os/scripts/mkimage-alpine.bash  /sandbox/base_os/build_dir/scripts/mkimage-alpine.bash
    fi  
```
The mkimage-alpine.bash takes a list of packages and installs them in a sbubdirectory. 

rootfs="$(mktemp -d "${TMPDIR:-/var/tmp}/alpine-docker-rootfs-XXXXXXXXXX")"
apk --root "$rootfs"

The result is a tarball. 

### prepare 

The aboove build script is then used to to create a minimal build container. 
For debug and troubleshooting a local copy is stored by podman save. 

```
builder:  clean $(BUILD_CONTAINER_FILE)
        cd $(BUILDER_DIR) && podman build -t ${BUILDER_IMAGE} -f Containerfile .
        mkdir -p tools
        rm -f tools/${BUILDER_IMAGE}.tar
        podman save ${BUILDER_IMAGE} -o tools/${BUILDER_IMAGE}.tar
```
### public build 

Binary packages are installed here from the repository specified in the settings file. 
The apk packaga manager keep track of all dependencies, when complete a list of all packages 
are stored in os.apk 

### download
All packages listed in os.apk are download from main and community repository. 
In addition to packages it also retrieves APKINDEX.tar.gz 

download.bash
```
FS=$'\n' read -d '' -r -a arr < sbom/os.apk

repo+=("main")
repo+=("community")
```
### private build 
This is basicly the same as public build, however all packages are retrieved from a local directory. 
It also adds a bom.sh script that extract additional data from the package manager, such as project url. 

### test
currently it is just executues bom.sh and stores the result in sbom/os.bom as plain text. 

### aggregate

APKINDEX:tar.gz from main and community repository are added to apkindex.tar. This resulting tarfile path is passed as a parameter to aggregate_bom.py 
together with os.bom, settings and packages. 

All data about binary packages are now collected and stored in aggregated.json 


```
if [ "$1" = 'aggregate' ]; then                                                                                                                                         
       cd /sandbox/base_os/download  && find . -name APKINDEX.tar.gz | cut -c3- |  tar cf /sandbox/base_os/sbom/apkindex.tar -T -
       exec python3 /opt/base_os/scripts/aggregate_bom.py  --pkgindex /sandbox/base_os/sbom/apkindex.tar \
                                                           --desired /sandbox/base_os/config/packages     \
							   --config /sandbox/base_os/config/settings  \
							   --resolved /sandbox/base_os/sbom/os.bom \
							   --output /sandbox/base_os/sbom/aggregated.json                                                ```           ```                

                                                              

## Prepare debug and test 

The resolved is data driven, therefore is is important to use production data when testing. 

Development follow the **onion** model.  Development starts from the inside, when done, the code is 

deployed as a container. 


### Install python modules 

Some of the modules ( get_file_git.py )  have dependencies, therefore pip install must be executed to prevent inconsistency issues. 

```
import bomres.lib.git_manager as git_manager
```

There is a rule in the Makefile for installing python modules on your development host

```
make pip 
	cd ../../build/bomres  && pip3 install . )
```



### Reproduce the error in a sandbox 

In this example product and tool directories will be created under /opt/sandbox 

```
$ mkdir -p /opt/sandbox
$ podman run  --rm docker.io/bomres/base_os_alpine make > Makefile
$ make config 
$ make build 
$ make resolv 
$ make tool_config 
$ make tool_build
```

```
make[1]: Entering directory '/opt/sandbox'
Traceback (most recent call last):
  File "/opt/base_os/scripts/aggregate_bom.py", line 665, in <module>
    sys.exit(main())
  File "/opt/base_os/scripts/aggregate_bom.py", line 648, in main
    format_dep(
  File "/opt/base_os/scripts/aggregate_bom.py", line 493, in format_dep
    if 'apkindex' in metadata and s_patch[0] == 'r':
IndexError: string index out of range
make[1]: *** [Makefile:56: _aggregate] Error 1
make[1]: Leaving directory '/opt/sandbox'
make: *** [Makefile:129: tool_aggregate] Error 2

```

Something went wrong when the tool container was created. 



## Retrieve source 

The code is located on github, start by creating a fork and when done a pull request. 

The problem is related to python, and all python code resides in test/python. 

```
$ git clone https://github.com/hans-lammda/bomres.git
$ cd services/sbom_resolver/service/test/python

```

Edit Makefile to reflect location of sandbox and which container to debug/test. 



```
SANDBOX=/opt/sandbox
TARGET=product
TARGET=tool
```



```
aggregate:
        python3  ../../build/bomres/bomres/lib/aggregate_bom.py  \
                --pkgindex $(SANDBOX)/$(TARGET)/build/base_os/sbom/apkindex.tar \
                --desired $(SANDBOX)/$(TARGET)/build/base_os/sbom/os.conf  \
                --resolved $(SANDBOX)/$(TARGET)/build/base_os/sbom/os.bom \
                --config $(SANDBOX)/$(TARGET)/build/base_os/config/settings \
                --output $(SANDBOX)/$(TARGET)/build/base_os/sbom/aggregated.json \
                --debug


```



The code should now have access to the same data as the container, verify that the **exact** same problem could be reproduced 



```
make aggregate
python3  ../../build/bomres/bomres/lib/aggregate_bom.py  --pkgindex /opt/sandbox/tool/build/base_os/sbom/apkindex.tar    --desired /opt/sandbox/tool/build/base_os/sbom/os.conf  \
                          --resolved /opt/sandbox/tool/build/base_os/sbom/os.bom  --config /opt/sandbox/tool/build/base_os/config/settings  --output /opt/sandbox/tool/build/base_os/sbom/aggregated.json #  --debug
Traceback (most recent call last):
  File "/home/hans/development/git-clones/bomres/services/sbom_resolver/service/test/python/../../build/bomres/bomres/lib/aggregate_bom.py", line 669, in <module>
    sys.exit(main())
  File "/home/hans/development/git-clones/bomres/services/sbom_resolver/service/test/python/../../build/bomres/bomres/lib/aggregate_bom.py", line 652, in main
    format_dep(
  File "/home/hans/development/git-clones/bomres/services/sbom_resolver/service/test/python/../../build/bomres/bomres/lib/aggregate_bom.py", line 497, in format_dep
    if 'apkindex' in metadata and s_patch[0] == 'r':
IndexError: string index out of range
make: *** [Makefile:41: aggregate] Error 1

```



## Analyze problem 

The resolver code is not stable, it is still a early prototype. The code is not clean, therefore you should start by analyzing the data. 



## Input data 

The product was generated, but not the tool 

```
$(SANDBOX)/$(TARGET)/build/base_os/sbom/os.bom 
a,alpine,,,,alpine_linux_3.16,
The data should look like below 
a,alpine,lighttpd,1.4.64,r0,alpine_linux_3.16,https://lighttpd.net
```

The build container transfer control to the product and tool  container for 
letting the package manager report installed packages. 

There is is different versions of awk in core utils and busybox. 


| Tool | version         | Comment                                                      |
| ---- | --------------- | ------------------------------------------------------------ |
| awk  | GNU Awk 5.1.1   | This version of awk comes from core-utils in the tools container |
| awk  | BusyBox v1.35.0 | This is part of busybox from the product container.          |



## Rectify the problem 

tools/base_os_alpine/build/scripts/bom.sh

### Old code 

```
LONG_VERSION=`apk info $p  | grep -v WARNING | awk -v pack="$p" 'BEGIN {RS="" FS="\n" }  {for (i=1,j=2,k=0; i<=NF; i++,j++i,k++) { if ($i == "webpage:") {printf "%s",$k ; exit }} }' 2> /dev/null`

URL=`apk info $p  | grep -v WARNING | awk -v pack="$p" 'BEGIN {RS="" FS="\n" }  {for (i=1,j=2,k=0; i<=NF; i++,j++i,k++) { if ($i == "webpage:") {printf "%s",$j ; exit }} }' 2> /dev/null`
```





### New code 

```
LONG_VERSION=`apk info $p 2> /dev/null | grep  description | awk '{print $1}'`
URL=`apk info $p 2> /dev/null | grep '://' `
VER_REV=`echo $LONG_VERSION | sed "s/^\$p-//"`
VERSION=`echo $VER_REV | awk -F\- '{print $1}'`
REVISION=`echo $VER_REV | awk -F\- '{print $2}'`
```



Test the updated bom.sh for Gnu AWK 

```
podman run --rm -i -t  "alpine_sandbox_base_os_tool":"3.16.1" sh
```



Test for Busybox 

```
docker run -i -t docker.io/bomres/base_os_alpine  sh
```



# Finish 

commit code to your personal repo and create a pull request 

also update the docker images 


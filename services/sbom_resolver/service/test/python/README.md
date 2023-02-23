

# Test 

The resolved is data driven, therefore is is important to use production data when testing. 

Development follow the **onion** model.  Development starts from the inside, when done, the code is 

deployed as a container. 



## Prepare debug and test 

### Install python modules 

Some of the modules ( get_file_git.py )  have dependencies, therefore pip install must be executed to prevent inconsistency issues. 

```
import bomres.lib.git_manager as git_manager
```

There is a rule in teh Makefile for installing python modules on your development host

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


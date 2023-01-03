# bomres - A Software Bill-of-Material Resolver

## Overview

bomres is a Software Bill-of-Material (SBoM) Resolver specifically designed for Alpine-based container images. It allows to create a detailed SBOM based on two sets of information:

1. A short list of key software dependencies which must be present in a resulting Alpine image, and
2. build meta-data taken from the Alpine aports repository.

bomres processes, correlates and combines these information in conjunction with information provided by the apk package manager to generate a detailed SBoM, exposing more information about the image than provided by the package manager itself. In particular, the resulting SBoM containes information about the location of the source code of a package, patches applied by the Alpine community and security information.


### Architecture

bomres consists of two components:

1. an **Alpine image builder** which creates an Alpine image containing all packages (and their dependencies) listed in a "desired bill-of-material" file, and
2. the actual **SBoM resolver** which uses information provided by the Alpine package manager and generated during the previous build process and combines these with additional meta-data hosted in the Aports repository.

### Workflow

The overall workflow is shown in the figure below:
![Workflow](docs/figures/workflow.png)


### Deployment options

bomres can be deployed in three different scenarios:

1. As a standalone toolset packaged in two containers,
2. As a standalone service exposing a RESTful API, or
3. As a scalable service deployed on Kubernetes

More detailed documentation on how to deploy each scenario to come soon.


## Usage

### Prerequisities

Ubuntu 22.04.1 LTS

podman version 3.4.4



### Containerized tool

To run bomres as a containerized toolset, perform the following steps:

```bash
$ podman run  --rm docker.io/bomres/base_os_alpine make > Makefile
$ make config
$ vim product/build/base_os/config/packages
$ vim product/build/base_os/config/settings
$ make build
$ make resolve
$ make download_source # Download all source code, including patches
```

### Service

To run bomres as a service 

```bash
$ podman run -i -t -p 8082:8080 docker.io/bomres/alpine_resolver server
$ firefox http://localhost:8082/resolver/alpine/v1/ui/ 
```

### CI/CD Integration 

The two docker images could be invoked inside another container

```bash
$ cd tools/base_os_alpine/test/podman  
$ make run 
```




## Contributing

bomres is current in early stages and primarily meant to demonstate the concept. All contributions, PRs, issues, comments, are welcome.



```bash

```


## License

bomres is available under the Apache 2.0 license.

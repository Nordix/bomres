# bomres - A Software Bill-of-Material Resolver

## Overview

bomres is a Software Bill-of-Material (SBOM) Resolver specifically designed for Alpine-based container images. It allows to create a detailed SBOM based on two sets of information:

1. A short list of key software dependencies which must be present in a resulting Alpine image, and
2. build meta-data taken from the Alpine aports repository.

bomres processes, collelates and combines these information in conjunction with information provided by the apk package manager to generate a detailed SBOM, exposing more information about the image than the package manager alone can expose. In particular, it containes information about the location of the source code of a package, patches applied by the Alpine community and security information.

TODO: add figure here


## Use Cases

The information encoded in the SBOM created by bomres can be used to realize the following use case:

### Re-Building software images in an isolated environment

TBD

TODO: add figure here


## Usage

bomres comprises two container images

1. the Alpine os builder, and
2. the SBOM resolver

Prebuilt versions of both images are hosted publicly.

To run an example, execute the following steps:

```bash
cd bomres/services/sbom_resolver/service/test
make tool
```

## Building from source

To build the alpine builder container and the sbom-resolver container, run the following:

```bash
cd bomres/tools/base_os_alpine
make local
```


## Contributing

bomres is current in early stages and primarily meant to demonstate the concept. All contributions, PRs, issues, comments, are welcome.


## License

bomres is available under the Apache 2.0 license.

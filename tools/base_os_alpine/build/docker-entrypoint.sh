#!/bin/sh

if [ "$1" = 'init' ]; then
    if test ! -d /sandbox/base_os ; then 
       mkdir -p /sandbox/base_os 
    fi 
    if test ! -f /sandbox/base_os/download.bash ; then 
       cp -f /opt/base_os/scripts/download.bash  /sandbox/base_os/download.bash
    fi 
    if test ! -d /sandbox/base_os/sbom ; then 
       mkdir -p /sandbox/base_os/sbom 
    fi 
    if test ! -f /sandbox/base_os/templates ; then 
       mkdir -p /sandbox/base_os/templates
       cp -f /opt/base_os/templates/images/*  /sandbox/base_os/templates
    fi 
    if test ! -f /sandbox/base_os/build_dir ; then 
       mkdir -p /sandbox/base_os/build_dir/scripts
       cp -f /opt/base_os/scripts/apk-install  /sandbox/base_os/build_dir/scripts/apk-install
       cp -f /opt/base_os/scripts/mkimage-alpine.bash  /sandbox/base_os/build_dir/scripts/mkimage-alpine.bash
    fi 
    if test ! -f /sandbox/base_os/payload_dir ; then 
       mkdir -p /sandbox/base_os/payload_dir/scripts
       cp -f /opt/base_os/scripts/bom.sh  /sandbox/base_os/payload_dir/scripts/bom.sh
    fi 
    if test ! -f /sandbox/base_os/config ; then 
       mkdir -p /sandbox/base_os/config
    fi 
    if test ! -f /sandbox/base_os/config/settings ; then 
       cp -f /opt/base_os/templates/config/v3.14  /sandbox/base_os/config/settings
    fi 
    if test ! -f /sandbox/base_os/config/packages ; then 
       cp -f /opt/base_os/templates/images/minimal  /sandbox/base_os/config/packages
    fi 
    if test ! -f /sandbox/base_os/Makefile ; then 
       cp -f /opt/base_os/templates/makefiles/Makefile  /sandbox/base_os/Makefile
    fi 
elif [ "$1" = 'aggregate' ]; then
       cd /sandbox/base_os/download  && find . -name APKINDEX.tar.gz | cut -c3- |  tar cf /sandbox/base_os/sbom/apkindex.tar -T -
       exec python3 /opt/base_os/scripts/aggregate_bom.py  --pkgindex /sandbox/base_os/sbom/apkindex.tar    --desired /sandbox/base_os/config/packages   --config /sandbox/base_os/config/settings  --resolved /sandbox/base_os/sbom/os.bom   --output /sandbox/base_os/sbom/aggregated.json 

elif [ "$1" = 'config' ]; then
    if test ! -f /sandbox/base_os/config ; then 
       mkdir -p /sandbox/base_os/config
    fi 
    if test ! -f /sandbox/base_os/config/settings ; then 
       cp -f /opt/base_os/templates/config/v3.14  /sandbox/base_os/config/settings
    fi 
    if test ! -f /sandbox/base_os/config/packages ; then 
       cp -f /opt/base_os/templates/images/minimal  /sandbox/base_os/config/packages
    fi 
elif [ "$1" = 'make' ]; then
    cat /opt/base_os/templates/makefiles/Makefile.bootstrap
elif [ "$1" = 'help' ]; then
    echo ""
    echo "make :     Outputs a simple Makefile for building and resolving Alpine "
    echo "init :     Create a directory structure with tools needed to build a Alpine Base Image"
    echo "config:    Add templates for Desired SBOM and "
    echo "aggregate: Concatenate Desired SBOM , Resolved SBOM and all APKINDEX.tar.gz files used for build "
    echo ""
else
    exec "$@"
fi

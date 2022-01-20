#!/usr/bin/env bash


. config/settings

localRepo="download/alpine"
mkdir -p ${localRepo}
repo=()
repo+=("main")
repo+=("community")
for rep in "${repo[@]}" ; do
  lpath=v${ALPINE_VERSION}/${rep}/${ARCH}/APKINDEX.tar.gz
  localFilePath=${localRepo}/${lpath}
  path=${REPO_URL}/${lpath}
  if  test -f ${localFilePath} ; then 
    echo "${localFilePath} Exists"
   else 
    mkdir -p `dirname ${localFilePath}`
    if  curl --fail --silent -X GET ${path} -o ${localFilePath} > /dev/null ; then
      echo "${localFilePath} OK"
    else  
      echo "${localFilePath} Error"
    fi  
  fi  
done

## output of apk info -v 
# musl-1.1.16-r13
# busybox-1.26.2-r7
# alpine-baselayout-3.0.4-r0
# alpine-keys-2.1-r1


IFS=$'\n' read -d '' -r -a arr < sbom/os.apk

for microservice in "${arr[@]}" ; do

  lpath=v${ALPINE_VERSION}/main/${ARCH}
  path=${REPO_URL}/${lpath}/${microservice}.apk
  main_path=${path}
  if  curl --fail --silent --head ${path} > /dev/null ; then
    echo  ${path} > /dev/null
  else
    lpath=v${ALPINE_VERSION}/community/${ARCH}
    path=${REPO_URL}/${lpath}/${microservice}.apk
    if  curl --fail --silent --head ${path} > /dev/null ; then
      echo  ${path} > /dev/null
    else
      echo "*******************************"
      echo ""
      echo "The package [${microservice}] is missing, cannot continue "
      echo ""
      echo ""
      echo "Please check public repositiries below for updates"
      echo ""
      echo -e "\t${main_path}"
      echo -e "\t${path}"
      echo ""
      echo ""
      echo "Exiting with errorcode 1"
      echo ""
      echo "*******************************"
      echo ""
      echo ""
      echo ""
      exit 1 
    fi
  fi
  localFilePath=${localRepo}/${lpath}/${microservice}.apk
  if  test -f ${localFilePath} ; then 
    echo "${localFilePath} Exists"
   else 
    
    mkdir -p `dirname ${localFilePath}`
    if  curl --fail --silent -X GET ${path} -o ${localFilePath} > /dev/null ; then
      echo "${localFilePath} OK"
    else  
      echo ""
      echo "Unable to download ${localFilePath}, cannot continue "
      echo ""
      exit 1 
    fi  
  fi  
done
    

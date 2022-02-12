#!/bin/sh

if [ "$1" =    'aggregate' ]; then
   exec sbom-resolver-aggregate_bom  --pkgindex /sbom/apkindex.tar   --desired /sbom/os.conf          --resolved /sbom/os.bom   --config /sbom/settings --output /sbom/aggregated.json 

elif [ "$1" =  'clone' ]; then
   if [ "$#" -eq 1 ]; then
     exec  sbom-resolver-git_manager  --cmd clone --dir /mnt/alpine/src --url https://git.alpinelinux.org/aports
   elif [ "$#" -eq 2 ]; then
     exec  sbom-resolver-git_manager  --cmd clone --dir /mnt/alpine/src --url "$2"
   fi
elif [ "$1" = 'index' ]; then
   # Input: tarball of all APKINDEX.tar.gz used in binary build , Output: One JSON file covering all packages used by the build 
   sbom-resolver-aggregate_bom       --pkgindex /sbom/apkindex.tar   --output   /sbom/index.json 

   # Checkout all APKINDEX files for each packages listed in index.json , Output: directory structure with all packages and APKINDEX with commit hash extension 
   sbom-resolver-create_apkcache     --apkindex /sbom/index.json     --src      /mnt/alpine/src        --checkout   /mnt/alpine/checkout --cache /mnt/alpine/cache

   # Combine information extracted from APKINDEX ( index.json ) and APORTS source , Output is a JSON with all info from APKINDEX and APORTS, named of hashed value of apkindex.tar
   exec sbom-resolver-parse_apkbuild --apkindex /sbom/index.json     --checkout /mnt/alpine/checkout   --cache      /mnt/alpine/cache 


elif [ "$1" = 'resolve' ]; then
   exec sbom-resolver-resolve_bom    --packages /sbom/aggregated.json  --cache /mnt/alpine/cache         --output /sbom/resolved.json 

elif [ "$1" = 'download' ]; then
   if [ "$#" -eq 1 ]; then
      exec sbom-resolver-get_file_git  --src /mnt/alpine/src --resolved  /sbom/resolved.json   --output /source  --mode all  --debug
   elif [ "$#" -eq 2 ]; then
      if [ "$2" = "internal"  ]; then
         exec sbom-resolver-get_file_git  --src /mnt/alpine/src --resolved  /sbom/resolved.json   --output /source  --mode internal  --debug
      elif [ "$2" = "external"  ]; then
         exec sbom-resolver-get_file_git  --src /mnt/alpine/src --resolved  /sbom/resolved.json   --output /source  --mode external  --debug
      fi
   elif [ "$#" -eq 3 ]; then
      if [ "$2" = "internal"  ]; then
         if [ "$3" = "code"  ]; then
            exec sbom-resolver-get_file_git  --src /mnt/alpine/src --resolved  /sbom/resolved.json   --output /source  --mode internal --type code  --debug
         elif [ "$3" = "patch"  ]; then
            exec sbom-resolver-get_file_git  --src /mnt/alpine/src --resolved  /sbom/resolved.json   --output /source  --mode internal  --type patch --debug
         fi
      elif [ "$2" = "external"  ]; then
         if [ "$3" = "code"  ]; then
            exec sbom-resolver-get_file_git  --src /mnt/alpine/src --resolved  /sbom/resolved.json   --output /source  --mode external  --type code --debug
         elif [ "$3" = "patch"  ]; then
            exec sbom-resolver-get_file_git  --src /mnt/alpine/src --resolved  /sbom/resolved.json   --output /source  --mode external --type patch --debug 
         fi
      fi
   fi

elif [ "$1" = 'make' ]; then
    cat /Makefile.bootstrap
elif [ "$1" = 'help' ]; then
   echo ""
   echo "init    :  Create a directory structure with tools needed to build a Alpine Base Image"
   echo "make    :  Outputs a simple Makefile for building and resolving Alpine "
   echo "download:  "
   echo "           internal: Download all code and patches from Alpine Aports repository "
   echo "           external: Download all code and patches from external sources"
   echo "resolve :  Enrich the aggregated SBOM with information from Alpine Aports "
   echo "clone   :  Clone Alpine aports repository to local directory"
   echo "        :  Specify alternative path, default is https://git.alpinelinux.org/aports"
   echo "index   :  Create metadata needed for faster resolve "
   echo "server  :  Listen on port 8080 for HTTP requests , singlethread"
   echo "uwsgi   :  Listen on port 8080 for HTTP requests , multithread"
   echo ""
elif [ "$1" = 'server' ]; then
   exec python3 app.py
elif [ "$1" = 'uwsgi' ]; then
   exec uwsgi --socket 0.0.0.0:8080 --protocol=http --wsgi-file wsgi.py --master --processes 4 --threads 2
else
    exec "$@"
fi


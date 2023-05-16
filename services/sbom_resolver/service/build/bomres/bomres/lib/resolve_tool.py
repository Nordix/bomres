import sys
import os
import re
import pprint
import json
import argparse

import shutil
from pathlib import Path



# python3 get_file_git.py  --src /tmp/alpine/src --resolved
# /tmp/resolved.json  --output internal  --debug --mode internal

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

#
# Info about exceptions in string
#

import requests as req


#
# JSON import
#
def import_json(input_file):
    try:
        fp = open(input_file, "r")
        data = fp.read()
        fp.close()
        y = json.loads(data)
    except BaseException:
        return {}
    else:
        return y


ALPINE_REPO_NAME = "aports"

# Dict for parsing command line args and options.

args_options = {
    'opt':
    [
        {'long': '--debug', 'help': 'Debug mode'},
        {'long': '--packages', 'help': 'Packages'},
        {'long': '--settings', 'help': 'Settings'}
    ],
    'opt_w_arg':
    [

        {'long': '--resolved', 'help': 'Resolved SBOM in JSON Format ',
         'meta': 'resolved', 'required': True}
    ]
}


def parse_cmdline():

    parser = argparse.ArgumentParser(description='Bom Utility ')

    for opt in args_options['opt']:
        parser.add_argument(opt['long'], help=opt['help'], action="store_true")
    for opt_w_arg in args_options['opt_w_arg']:
        parser.add_argument(opt_w_arg['long'], help=opt_w_arg['help'],
                            metavar=opt_w_arg['meta'],
                            required=opt_w_arg['required'])

    args = parser.parse_args()
    return args




def get_tools(sbom,  debug):

    #
    # Populate cache with external code, required for rebuild
    #

    primary_deps = [] 
    for comp in sbom['dependencies']: 
     product = comp['pipeline']['product'] 
     parent = comp['pipeline']['aggregator']['alpine']['parent'] 
     if parent not in primary_deps and product == parent: 
        primary_deps.append(parent) 


    second_main = {} 
    for comp in sbom['dependencies']: 
     product = comp['pipeline']['product'] 
     if product  in primary_deps: 
       parent = comp['pipeline']['aggregator']['alpine']['parent'] 
       if parent in primary_deps: 
        develop = comp['pipeline']['aggregator']['alpine']['depends']['develop']
        for lib in develop: 
          dev_parent = develop[lib]['parent'] 
          if dev_parent not in primary_deps: 
            if dev_parent not in second_main: 
             second_main[dev_parent] = {}
             second_main[dev_parent][product] = []
             second_main[dev_parent][product].append(lib) 
            else: 
             if product not in second_main[dev_parent]: 
               second_main[dev_parent][product] = []
             second_main[dev_parent][product].append(lib) 


    # Different repos have different repository states
    s = ""
    if 'tools' in sbom: 
      s =  s + "# Autogenerated SBOM" + "\n\n" 

      s =  s + "#" + "\n" 
      s =  s + "#" + "\n" 
      tmp = sbom["metadata"]["aggregator"]["alpine"]["settings"]

      # Write section in desired tool SBOM that connects to product 

      for k in tmp: 
       s =  s + "# " + k + "=" + tmp[k] + "\n" 
      s =  s + "#" + "\n\n" 

      s =  s + "# Minimal Alpine Base OS" + "\n\n" 
      s =  s + "alpine-base" + "\n" 
      s =  s + "util-linux" + "\n" 
      s =  s + "\n# Binary build    \n" 
      s =  s + "bash" + "\n" 
      s =  s + "tzdata" + "\n" 
      s =  s + "xz" + "\n" 
      s =  s + "curl" + "\n" 
      s =  s + "apk-tools" + "\n" 
      s =  s + "#" + "\n\n" 

      s =  s + "# Common Build tools" + "\n\n" 
      s =  s + "alpine-sdk" + "\n" 
      s =  s + "build-base" + "\n" 
      s =  s + "abuild" + "\n" 
      s =  s + "\n#-----------------------------------------------------------------\n" 
      s =  s + "\n# Development tools" + "\n\n" 
      s =  s + "\n# Additional tools needed for specific packages during build " + "\n" 
      s =  s + "\n#-----------------------------------------------------------------\n\n" 
      tools = {} 
      for id in sbom['tools']:
        i = 0 
        for comp in sbom['tools'][id]:
          pkg = sbom['tools'][id][i]['child'] 
          if pkg  not in tools: 
             tools[pkg] = [] 
          if id not in tools[pkg]: 
              tools[pkg].append(id) 
          i = i + 1 
      for id in tools:
        s = s + "# "  + " ".join(tools[id]) + "\n"
        s = s + id + "\n\n"

      if len(second_main) > 0 : 
        s =  s + "\n#-----------------------------------------------------------------\n" 
        s =  s + "\n# Secondary product dependencies" + "\n\n" 
        s =  s + "\n# Additional packages needed for building the product " + "\n" 
        s =  s + "\n# Packages listed here must either be removed ( hardening ) or included in product desired SBOM" + "\n" 
        s =  s + "\n#-----------------------------------------------------------------\n\n" 
        for sec in second_main: 
            s = s + "# "  + sec + "\n"
            for prim in second_main[sec]: 
              if prim != sec: 
                s = s + "#   "  + prim + "         " + " ".join(second_main[sec][prim]) + "\n"
            s = s +  "\n"
        s = s +  "\n"
        for sec in second_main: 
            s = s + sec + "\n"
          
    return s



def get_settings(sbom,  debug):

    #
    # Populate cache with external code, required for rebuild
    #

    # Different repos have different repository states
    s = ""
    if 'tools' in sbom: 
      s =  s + "#" + "\n" 
      s =  s + "# This desired SBOM is generated from the complete product  SBOM" + "\n" 
      s =  s + "#" + "\n" 
      s =  s + "#" + "\n" 
      tmp = sbom["metadata"]["aggregator"]["alpine"]["settings"]
      for k in tmp: 
       if k == 'BASE_OS_IMAGE': 
         s =  s + "#" + "\n" 
         s =  s + "# _tool appended to product image name " + "\n" 
         s =  s + "#" + "\n" 
         s =  s +  k + "=\"" + tmp[k] + "_tool" + "\"\n" 
         s =  s + "#" + "\n" 
       else: 
         s =  s +  k + "=\"" + tmp[k] + "\"\n" 
    return s



def main():

    args = parse_cmdline()


    if args.resolved:
        resolved_sbom = import_json(args.resolved)
        if args.packages:
           tmp = get_tools(resolved_sbom,  args.debug)
           sys.stdout.write(tmp) 
        elif args.settings:
           tmp = get_settings(resolved_sbom,  args.debug)
           sys.stdout.write(tmp) 


    sys.exit(0)


if __name__ == '__main__':
    sys.exit(main())

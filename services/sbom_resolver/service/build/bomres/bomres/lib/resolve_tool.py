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
        {'long': '--debug', 'help': 'Debug mode'}
    ],
    'opt_w_arg':
    [

        {'long': '--resolved', 'help': 'Resolved SBOM in JSON Format ',
         'meta': 'resolved', 'required': True},
        {'long': '--output', 'help': 'Output directory',
         'meta': 'output', 'required': False}
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

    # Different repos have different repository states
    plist = [] 
    for id in sbom['dependencies']:
        if id['pipeline']['aggregator']['alpine']['parent'] not in plist: 
            plist.append(id['pipeline']['aggregator']['alpine']['parent'])
    return plist



def main():

    args = parse_cmdline()


    if args.resolved:
        resolved_sbom = import_json(args.resolved)
        tmp = get_tools(resolved_sbom,  args.debug)
        pprint.pprint(tmp) 


    sys.exit(0)


if __name__ == '__main__':
    sys.exit(main())

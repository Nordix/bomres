import sys
import os
import re
import pprint
import json
import argparse

from pathlib import Path


try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

 # Dict for parsing command line args and options.

args_options = {
    'opt':
    [
        {'long': '--debug', 'help': 'Debug mode'},
    ],
    'opt_w_arg':
    [

        {'long': '--packages', 'help': 'Aggregated SBOM ',
         'meta': 'packages', 'required': True},
        {'long': '--cache', 'help': 'Directory with metadata extracted from Aports and APKINDEX',
         'meta': 'cache', 'required': True},
        {'long': '--output', 'help': 'Result from Baazar',
         'meta': 'output', 'required': True}
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
        return None
    else:
        return y

#
# JSON Export
#


def export_json(inp):
    io = StringIO()
    y = json.dump(inp, io, skipkeys=False, ensure_ascii=True, check_circular=True, allow_nan=True, cls=None, indent=4,
                  separators=None, default=None)
    y = io.getvalue()
    return y

def list_of_tools(prod,alpine_dict): 
    tmp = [] 
    for kind in alpine_dict['map'][prod]['tools']: 
        for pkg in alpine_dict['map'][prod]['tools'][kind]: 
            # APKBUILD for libc-dev have some empty variables listed in makedepends
            temp = alpine_dict['map'][prod]['tools'][kind][pkg]
            temp['child'] = pkg 
            tmp.append(temp) 
    return tmp


def mapper(comp_dict, alpine_dict, debug=False):

    tool_dict = {} 

    stats = {}
    stats['total'] = 0
    stats['miss'] = 0
    stats['product_version_match'] = 0
    stats['product_match'] = 0
    stats['children'] = 0
    stats['missing'] = {}
    stats['missing']['product'] = []
    stats['missing']['version'] = []

    if 'dependencies' in comp_dict:
        iterate = comp_dict['dependencies']

    for comp in iterate:

        if 'pipeline' in comp and 'domain' in comp['pipeline']:
            kind = comp['pipeline']['domain']

            if kind in ['linux']:
                stats['total'] = stats['total'] + 1

                prod = comp['pipeline']['product']
                ver = comp['pipeline']['version']
                vendor = comp['pipeline']['vendor']
                try:
                    parent = comp['pipeline']['aggregator']['alpine']['parent']
                except BaseException:
                    # Mismatch between os.bom and apkindex , this is bad
                    stats['miss'] = stats['miss'] + 1
                    stats['missing']['product'].append(prod)
                    continue
                if debug:
                    sys.stdout.write("Processing  [%s]  [%s]: " % (prod, ver))
                    pprint.pprint(comp)

                if prod != parent:
                    stats['children'] = stats['children'] + 1
                    comp['pipeline']['aggregator']['info'] = {}
                    comp['pipeline']['aggregator']['info']['text'] = "This package is a subpackage of %s" % comp['pipeline']['aggregator']['alpine']['parent']
                    if debug:
                        sys.stdout.write("This is children of parent %s APKINDEX\n" %
                                         comp['pipeline']['aggregator']['alpine']['parent'])
                    continue

                if prod not in alpine_dict['map']:
                    # Package build not found in aports
                    stats['miss'] = stats['miss'] + 1
                    stats['missing']['product'].append(prod)
                    comp['aggregate'] = {}
                    comp['aggregate']['match'] = 'miss'
                    if debug:
                        sys.stdout.write("Miss [%s]\n" % parent)
                else:
                    # Subpackages defined in aports
                    if alpine_dict['map'][prod]['parent'] != prod:
                        if 'depend' in alpine_dict['map'][prod]:
                            comp['aggregate']['depend'] = alpine_dict['map'][prod]['depend']
                            #pprint.pprint(alpine_dict['map'][prod]['depend']) 
                        stats['children'] = stats['children'] + 1
                        comp['aggregate'] = {}
                        comp['aggregate']['parent'] = alpine_dict['map'][prod]['parent']
                        comp['aggregate']['info'] = {}
                        comp['aggregate']['info']['text'] = "This package is a subpackage of %s" % alpine_dict['map'][prod]['parent']
                        if debug:
                            sys.stdout.write(
                                "This is children of parent %s (Aport) \n" % alpine_dict['map'][prod]['parent'])
                        continue
                    # Subpackages defined in APKINDEX

                    elif comp['pipeline']['aggregator']['alpine']['parent'] != prod:
                        stats['children'] = stats['children'] + 1
                        comp['aggregate']['info'] = {}

                        if 'depend' in alpine_dict['map'][prod]:
                            comp['aggregate']['depend'] = alpine_dict['map'][prod]['depend']

                        comp['aggregate']['info']['text'] = "This package is a subpackage of %s" % comp['pipeline']['aggregator']['alpine']['parent']
                        if debug:
                            sys.stdout.write("This is children of parent %s APKINDEX\n" %
                                             comp['pipeline']['aggregator']['alpine']['parent'])
                        continue

                    if ver == alpine_dict['map'][prod]['pkgver']:
                        stats['product_version_match'] = stats['product_version_match'] + 1
                        comp['aggregate'] = {}
                        comp['aggregate']['match'] = 'product_version_match'
                        comp['aggregate']['parent'] = alpine_dict['map'][prod]['parent']

                        if 'repolink' in alpine_dict['map'][prod]:
                            comp['aggregate']['repolink'] = alpine_dict['map'][prod]['repolink']

                        if 'pkgname_alias' in alpine_dict['map'][prod]:
                            comp['aggregate']['pkgname_alias'] = alpine_dict['map'][prod]['pkgname_alias']

                        if 'depend' in alpine_dict['map'][prod]:
                            comp['aggregate']['depend'] = alpine_dict['map'][prod]['depend']

                        if 'download' in alpine_dict['map'][prod]:
                            comp['aggregate']['source'] = alpine_dict['map'][prod]['download']
                        if 'security' in alpine_dict['map'][prod]:
                            if 'info' not in comp['aggregate']:
                                comp['aggregate']['info'] = {}
                            comp['aggregate']['info']['secfixes'] = alpine_dict['map'][prod]['security']
                        if 'checksum' in alpine_dict['map'][prod]:
                            if len(alpine_dict['map'][prod]['checksum']) > 0: 
                               comp['aggregate']['source']['checksum'] = alpine_dict['map'][prod]['checksum'] 
                        if 'license' in alpine_dict['map'][prod]:
                            if 'info' not in comp['aggregate']:
                                comp['aggregate']['info'] = {}
                            comp['aggregate']['info']['license'] = alpine_dict['map'][prod]['license']
                        if debug:
                            sys.stdout.write("Match\n")
                            pprint.pprint(alpine_dict['map'][prod])
                        if 'tools' in alpine_dict['map'][prod]:
                            temp = list_of_tools(prod,alpine_dict)
                            if len(temp) > 0: 
                               tool_dict[prod] = list_of_tools(prod,alpine_dict)
                    else:
                        comp['aggregate'] = {}
                        comp['aggregate']['match'] = 'product_match'
                        comp['aggregate']['info'] = {}
                        if 'security' in alpine_dict['map'][prod]:
                            comp['aggregate']['info']['secfixes'] = alpine_dict['map'][prod]['security']
                        stats['product_match'] = stats['product_match'] + 1
                        missing_version_dict = {}
                        missing_version_dict['product'] = [prod]
                        missing_version_dict['build'] = ver
                        missing_version_dict['found'] = alpine_dict['map'][prod]['pkgver']
                        stats['missing']['version'].append(
                            missing_version_dict)
                        if debug:
                            sys.stdout.write("Version missing [%s] [%s]\n" % (
                                ver, alpine_dict['map'][prod]['pkgver']))

    primary_deps = []
    for comp in comp_dict['dependencies']:
     product = comp['pipeline']['product']
     parent = comp['pipeline']['aggregator']['alpine']['parent']
     if parent not in primary_deps and product == parent:
        primary_deps.append(parent)


    second_main = {}
    for comp in comp_dict['dependencies']:
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

    comp_dict['tools'] = tool_dict
    comp_dict['stats'] = {}
    comp_dict['stats']['aggregate'] = stats
    comp_dict['stats']['resolver'] = {} 

    if len(second_main) > 0: 
       comp_dict['stats']['resolver']['status'] = False
       comp_dict['stats']['resolver']['secondary'] = second_main
    else: 
       comp_dict['stats']['resolver']['status'] = True
    return comp_dict

def main():

    args = parse_cmdline()

    if args.packages:
        comp_dict = import_json(args.packages)
        try:
            hash = comp_dict['metadata']['aggregator']['alpine']['apkindex']['hash']
        except BaseException:
            sys.stderr.write("Could not find any hash in %s" % args.packages)
            sys.exit(1)

    if args.cache:
        index_path = args.cache + "/APKINDEX-" + hash + ".json"
        if args.debug:
           sys.stdout.write("Cache file: %s\n" % index_path ) 
        cache_path = Path(index_path)
        if not cache_path.exists():
            sys.stderr.write(
                "Entry does not exists in cache, please generate index [%s]\n" % hash)
            sys.exit(1)

        alpine_dict = import_json(index_path)

    if args.output:
        comp_dict = mapper(comp_dict, alpine_dict, args.debug)
        out_json = export_json(comp_dict)
        fp = open(args.output, "w")
        fp.write(out_json)
        fp.close()

    sys.exit(0)


if __name__ == '__main__':
    sys.exit(main())

import os
import sys
import json
import re
import glob
import pprint
import subprocess
import yaml
import argparse

from pathlib import Path

import bomres.lib.apklib as apklib




try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

#
# Info about exceptions in string
#


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


#
# JSON Export
#
def export_json(inp):
    io = StringIO()
    y = json.dump(
        inp,
        io,
        skipkeys=False,
        ensure_ascii=True,
        check_circular=True,
        allow_nan=True,
        cls=None,
        indent=4,
        separators=None,
        default=str)
    y = io.getvalue()
    return y



 # Dictionairy for parsing command line args and options.
args_options = {
    'opt':
    [
        {'long': '--debug', 'help': 'Debug mode'},
    ],
    'opt_w_arg':
    [
        {'long': '--checkout', 'help': 'Directory of cached APKBUILD files with git extensions APKBUILD.deadbeef',
         'meta': 'checkout', 'required': True},
        {'long': '--cache', 'help': 'Directory with parsed APKINDEX files for quick lookup',
         'meta': 'cache', 'required': True},
        {'long': '--apkindex', 'help': 'apkindex.json',
         'meta': 'apkindex', 'required': True}
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


def get_package_repo_from_bom(bom):
    try:
        if "metadata" in bom:
            repo_list = list(bom["metadata"]["aggregator"]
                             ["alpine"]["aports"]["repo"].keys())
            repos = bom["metadata"]["aggregator"]["alpine"]["aports"]["repo"]
        elif 'data' in bom:
            repo_list = list(bom['data']["metadata"]["aggregator"]
                             ["alpine"]["aports"]["repo"].keys())
            repos = bom['data']["metadata"]["aggregator"]["alpine"]["aports"]["repo"]
        else:
            repo_list = list(bom.keys())
            repos = bom
    except BaseException:
        return {}
    else:
        tmp = {}
        for repo in repo_list:
            tmp[repo] = {}
            tmp[repo]['hash'] = repos[repo]['hash']
            tmp[repo]['tag'] = repos[repo]['tag']
        return tmp


def resolve_apkindex_file(filename, repo, repo_hash_dict):

    if repo in repo_hash_dict and 'hash' in repo_hash_dict[repo]:
        dirname = os.path.dirname(filename)
        return dirname + "/APKBUILD" + "." + repo_hash_dict[repo]['hash']
    else:
        return filename


def scan_aports(checkout_dir, apkindex):

    stats = {}
    stats['parse'] = {}
    stats['parse']['errors'] = []
    repos = apkindex['repos']
    repo_hash_dict = get_package_repo_from_bom(repos)
    result = {}
    cnt = 0
    cnt_package = 0
    cnt_repo = 0
    cnt_miss = 0

    for name in apkindex['index']: 
        repository = apkindex['index'][name]['repo'] 
        commit  = apkindex['index'][name]['commit'] 
        filename = checkout_dir + "/" + repository + "/" + name +  "/APKBUILD."  + commit
        apkbuild_path = Path(filename)

        # Try to open APKBUILD with individual commit 

        if apkbuild_path.exists():
           temp, parse_info = apklib.parse_apkbuild_manifest(name, repository, filename, repo_hash_dict, apkindex, "package")
           cnt_package = cnt_package +1 
        else: 
           filename_commit = resolve_apkindex_file(filename, repository, repo_hash_dict)
           apkbuild_path = Path(filename_commit)
           if apkbuild_path.exists():

              # Try to open APKBUILD with commit from repo tag  

              temp, parse_info = apklib.parse_apkbuild_manifest(name, repository, filename_commit, repo_hash_dict, apkindex, "repo")
              cnt_repo = cnt_repo + 1 
           else: 

              # Failed to resolve 
              temp, parse_info = apklib.parse_apkbuild_manifest(name, repository, filename_commit, repo_hash_dict, apkindex, "broken-link-between-aports-and-apkbuild")
              cnt_miss = cnt_miss + 1 
        cnt = cnt + 1
        if len(parse_info) > 0:
           stats['parse'][name] = parse_info
        if len(temp) > 0:
           result[name] = temp
           if name in apkindex['index'] and 'struct' in apkindex['index'][name]: 
              result[name]['struct'] = apkindex['index'][name]['struct']
           if 'childs' in result[name]:
              for child in result[name]['childs']:
                  child_entry = {}
                  child_entry['parent'] = name
                  result[child] = child_entry
           else:
             stats['parse']['errors'].append("Missing child %s" % name)

    stats['processed'] = cnt
    stats['packages'] = cnt_package
    stats['repos'] = cnt_repo
    stats['miss'] = cnt_miss
    return result, stats
   


def main():

    args = parse_cmdline()
    apkindex = import_json(args.apkindex)

    result = {}
    root_dir = args.cache
    result = {}
    result['map'], stats = scan_aports(args.checkout, apkindex)
    result['stats'] = stats
    result_json = export_json(result)
    cache_index_file = "%s/APKINDEX-%s.json" % (args.cache, apkindex['hash'])

    if len(result['map']) > 0:
        fp = open(cache_index_file, "w")
        fp.write(result_json)
        fp.close()
        sys.exit(0)
    else:
        sys.stderr.write(
            "Unable to create resolver database, is the repository cloned ?\n")
        sys.exit(1)


if __name__ == '__main__':
    main()

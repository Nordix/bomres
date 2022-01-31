import os
import sys
import json
import re
import glob
import pprint
import subprocess
import yaml
import argparse
import shutil
from pathlib import Path
import time
import datetime


try:
    import bomres.api.lib.git_manager as git_manager
except BaseException:
    import api.lib.git_manager as git_manager


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
# Execute any unix command from python
#
def run(cmd):
    child = subprocess.run([cmd], shell=True, check=False,
                           stdout=subprocess.PIPE, universal_newlines=True)
    tmp = {}
    tmp['exit_code'] = child.returncode
    tmp['stdout'] = child.stdout
    tmp['stderr'] = child.stderr
    return tmp


# root_dir needs a trailing slash (i.e. /root/dir/)


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


def prepare_aports_cache(aport_dir, dst_cache_dir, repo, commit_hash):
    path = Path(dst_cache_dir)
    path.mkdir(parents=True, exist_ok=True)

    for filename in glob.iglob(
            "%s/%s" % (aport_dir, repo) + '**/**', recursive=True):
        comp = filename.split('/')
        if 'APKBUILD' in comp:
            length = len(comp)
            if length > 3:
                repository = comp[length - 3]
                name = comp[length - 2]
                pkg = comp[length - 1]
                dst_file = "%s/%s/%s/%s.%s" % (dst_cache_dir,
                                               repository, name, pkg, commit_hash)
                dirname = os.path.dirname(dst_file)
                path = Path(dirname)
                path.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(filename, dst_file)


def create_cache(aports_src, pull_branch,
                 aports_checkout, aports_cache, apkindex):
    age = 0 
    cache_index_file = "%s/APKINDEX-%s.json" % (
        aports_cache, apkindex['hash'])
    cache_path = Path(cache_index_file)
    if cache_path.exists():
        check_age = import_json(cache_index_file) 
        if 'started' in check_age: 
           now = int(time.time()) 
           started = int(check_age['started'])
           age = now - started 
        return True, cache_index_file, None, age
    else:
        orm = git_manager.checkout(pull_branch, "%s/aports" % aports_src)
        if orm['status'] == False:
            return False, cache_index_file, None, age 

        git_manager.pull("%s/aports" % aports_src)
        aports_info = git_manager.info("%s/aports" % aports_src)
        for repo in apkindex['repos']:
            commit_hash = apkindex['repos'][repo]['hash']
            tmp = git_manager.checkout(commit_hash, "%s/aports" % aports_src)
            prepare_aports_cache(
                "%s/aports" %
                aports_src,
                aports_checkout,
                repo,
                commit_hash)
        return False, cache_index_file, aports_info, age 


def main():

    args = parse_cmdline()

    if args.branch:
        pull_branch = args.branch
    else:
        pull_branch = "master"

    apk_index_dict = import_json(args.apkindex)

    entry_exists, cache_index_file, aports_info = create_cache(
        args.src, pull_branch, args.checkout, args.cache, apk_index_dict)

   # Dictionairy for parsing command line args and options.
args_options = {
    'opt':
    [
        {'long': '--debug', 'help': 'Debug mode'},
    ],
    'opt_w_arg':
    [
        {'long': '--src', 'help': 'Directory to Alpine aports',
         'meta': 'src', 'required': True},
        {'long': '--checkout', 'help': 'Directory of cached APKBUILD files ',
         'meta': 'checkout', 'required': True},
        {'long': '--cache', 'help': 'Directory of lookup files in JSON',
         'meta': 'cache', 'required': True},
        {'long': '--apkindex', 'help': 'Alpine APKINDEX files in JSON ',
         'meta': 'apkindex', 'required': True},
        {'long': '--branch', 'help': 'Which branch to pull from  aports repo ',
         'meta': 'branch', 'required': False}
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


if __name__ == '__main__':
    main()

#
# gitpython should be consider
#
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
from datetime import datetime
import shutil
from pathlib import Path
import uuid


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


def info(root_dir):
    """
      {'branch': 'master', 'url': 'git://git.alpinelinux.org/aports', 'commit': 'f64ccb5f1b207ffee0a7d9c7576b35413a44b0e0', 'date': '2022-01-02 22:10:21 +0100'}
    """
    result = {}
    CWD = os.getcwd()
    os.chdir(root_dir)
    cmd = "git branch -l"
    tmp = run(cmd)
    if tmp['exit_code'] == 0:
        result['branch'] = tmp['stdout'].split()[1]

    cmd = "git remote -v"
    tmp = run(cmd)
    if tmp['exit_code'] == 0:
        line = tmp['stdout'].split('\n')[0]
        line = line.split()[1]
        result['url'] = line
    cmd = "git rev-parse HEAD"
    tmp = run(cmd)
    if tmp['exit_code'] == 0:
        line = tmp['stdout'].strip('\n')
        result['commit'] = line
        cmd = "git log -n1 --pretty=format:%%ai %s" % line
        tmp = run(cmd)
        if tmp['exit_code'] == 0:
            line = tmp['stdout'].strip('\n')
            result['date'] = line
    os.chdir(CWD)

    return result


def checkout(commit_hash, aports_dir):

    CWD = os.getcwd()
    result = {}
    try:
        os.chdir(aports_dir)
    except BaseException:
        result['status'] = False
        result['info'] = "Directory %s doest not exists" % aports_dir
        os.chdir(CWD)
        return result
    cmd = "git checkout %s" % commit_hash
    tmp = run(cmd)
    if tmp['exit_code'] == 0:
        line = tmp['stdout']
        result['status'] = True
        result['stdout'] = line
    else:
        result['status'] = False
    os.chdir(CWD)
    return result


def pull(directory):

    result = {}
    CWD = os.getcwd()
    os.chdir(directory)
    result = {}
    cmd = "git pull"
    result['cmd'] = cmd
    start_time = datetime.now()
    tmp = run(cmd)
    end_time = datetime.now()
    result['elapsed'] = 'Duration: {}'.format(end_time - start_time)
    if tmp['exit_code'] == 0:
        line = tmp['stdout']
        result['status'] = True
        result['stdout'] = line
    else:
        result['status'] = False
        result['stdout'] = tmp['stdout']
    os.chdir(CWD)
    return result


def clone(directory, url):

    result = {}

    path = Path(directory)
    path.mkdir(parents=True, exist_ok=True)
    CWD = os.getcwd()
    os.chdir(directory)
    result = {}
    cmd = "git clone %s" % url
    result['cmd'] = cmd
    start_time = datetime.now()
    tmp = run(cmd)
    end_time = datetime.now()
    result['elapsed'] = 'Duration: {}'.format(end_time - start_time)
    if tmp['exit_code'] == 0:
        uid = str(uuid.uuid4())
        fp = open("uid", mode='w', newline='')
        fp.write(uid)
        fp.close()
        line = tmp['stdout']
        result['uuid'] = uid
        result['status'] = True
        result['stdout'] = line
    else:
        result['status'] = False
        result['stdout'] = tmp['stdout']
    os.chdir(CWD)
    return result


def rm(directory, id):

    result = {}
    try:
        fp = open("%s/uid" % directory, "r")
        uid = fp.read()
        uid = uid.strip('\n')
        fp.close()
    except BaseException:
        uid = "X"

    if id != uid:
        result['status'] = False
        return result

    result['id'] = id
    try:
        shutil.rmtree(directory)
    except BaseException:
        result['status'] = False
    else:
        result['status'] = True
    return result


args_options = {
    'opt':
    [
        {'long': '--debug', 'help': 'Debug mode'},
    ],
    'opt_w_arg':
    [
        {'long': '--dir', 'help': 'Directory to Alpine aports',
         'meta': 'dir', 'required': True},
        {'long': '--url', 'help': 'Directory of cached APKBUILD files with git extensions APKBUILD.deadbeef',
         'meta': 'url', 'required': False},
        {'long': '--state', 'help': 'branch, tag or hash to checkout',
         'meta': 'state', 'required': False},
        {'long': '--cmd', 'help': 'command clone|checkout|delete',
         'meta': 'cmd', 'required': True},
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


def main():

    args = parse_cmdline()
    if args.cmd == "clone":
        tmp = clone(args.dir, args.url)
    elif args.cmd == "state":
        tmp = git_checkout(args.dir, args.state)
    elif args.cmd == "info":
        tmp = git_repo_info(args.dir)
    elif args.cmd == "delete":
        tmp = rm(args.dir)
    elif args.cmd == "pull":
        tmp = pull(args.dir)
    else:
        sys.exit(1)
    print(tmp)


if __name__ == '__main__':
    main()

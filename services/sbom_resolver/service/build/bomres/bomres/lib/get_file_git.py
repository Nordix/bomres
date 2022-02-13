import sys
import os
import re
import pprint
import json
import argparse

import shutil
from pathlib import Path

import bomres.lib.git_manager as git_manager


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
        {'long': '--pull', 'help': 'Pull'}
    ],
    'opt_w_arg':
    [

        {'long': '--src', 'help': 'Local clone of alpine repository',
         'meta': 'src', 'required': True},
        {'long': '--resolved', 'help': 'Resolved SBOM in JSON Format ',
         'meta': 'resolved', 'required': True},
        {'long': '--mode', 'help': 'internal, external or all dependencies',
         'meta': 'mode', 'required': False},
        {'long': '--type', 'help': 'retrieve code, patch or build (APKBUILD)',
         'meta': 'type', 'required': False},
        {'long': '--output', 'help': 'Output directory',
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


def get_internal_code(sbom, srcdir, dstdir, mode, src_type, debug):

    if debug: 
       sys.stdout.write("get_internal_code\n") 
    # Different repos have different repository states
    for repo in sbom['metadata']['aggregator']['alpine']['aports']['repo']:
        # There might be repos with no packages
        if debug: 
           sys.stdout.write("repo: %s\n" % repo) 
        if 'source' in sbom['metadata']['aggregator']['alpine']['aports']['repo'][repo]:
            source = sbom['metadata']['aggregator']['alpine']['aports']['repo'][repo]['source']
            hash = sbom['metadata']['aggregator']['alpine']['aports']['repo'][repo]['hash']
            git_manager.checkout(hash, "%s/%s" % (srcdir, ALPINE_REPO_NAME))

            # Iterate through all packages
            for package in source:
                index = package['index']
                if 'aggregate' in sbom['dependencies'][index] and 'source' in sbom['dependencies'][index][
                        'aggregate'] and 'internal' in sbom['dependencies'][index]['aggregate']['source']:
                    src = sbom['dependencies'][index]['aggregate']['source']['internal']
                    if debug: 
                      sys.stdout.write("src_type: %s\n" % src_type) 

                    if src_type in ['all', 'code']:
                        if debug: 
                           sys.stdout.write("source: %s\n" % package['package']) 
                        for code in src['code']:
                            hash = code['remote']['commit']['hash']
                            path = code['remote']['path']
                            dstpath = dstdir + "/" + path
                            srcpath = srcdir + "/" + ALPINE_REPO_NAME + "/" + path
                            directory = os.path.dirname(dstpath)
                            dirpath = Path(directory)
                            dirpath.mkdir(parents=True, exist_ok=True)
                            try:
                                shutil.copyfile(srcpath, dstpath)
                            except BaseException:
                                sys.stderr.write(
                                    "    **********Problem with component [%s] See TODO.txt\n" %
                                    package['package'])
                            else:
                                if debug:
                                    sys.stdout.write(
                                        "Internal code copied: %s\n" % dstpath)

                    if src_type in ['all', 'patch']:
                        for code in src['patch']:
                            hash = code['remote']['commit']['hash']
                            path = code['remote']['path']
                            dstpath = dstdir + "/" + path
                            srcpath = srcdir + "/" + ALPINE_REPO_NAME + "/" + path
                            directory = os.path.dirname(dstpath)
                            dirpath = Path(directory)
                            dirpath.mkdir(parents=True, exist_ok=True)
                            try:
                                shutil.copyfile(srcpath, dstpath)
                            except BaseException:
                                sys.stderr.write(
                                    "    **********Problem with component [%s] See TODO.txt\n" %
                                    package['package'])
                            else:
                                if debug:
                                    sys.stdout.write(
                                        "Internal patch copied: %s\n" % dstpath)

                    if src_type in ['all', 'build']:
                      src = sbom['dependencies'][index]['aggregate']['source']['internal']['build']
                      if len(src) != 0:
                        hash = src['remote']['commit']['hash']
                        path = src['remote']['path']
                        dstpath = dstdir + "/" + path
                        srcpath = srcdir + "/" + ALPINE_REPO_NAME + "/" + path
                        directory = os.path.dirname(dstpath)
                        dirpath = Path(directory)
                        dirpath.mkdir(parents=True, exist_ok=True)
                        try:
                            shutil.copyfile(srcpath, dstpath)
                        except BaseException:
                            sys.stderr.write(
                               "    **********Problem with component [%s] See TODO.txt\n" %
                               package['package'])
                        else:
                            if debug:
                               sys.stdout.write(
                                  "APKBUILD copied: %s\n" % dstpath)


def get_external_code(sbom, srcdir, dstdir, mode, src_type, debug):

    #
    #
    # {'local': {'path': 'main/musl/musl-v1.2.2.tar.gz', 'type': 'file'},
    # 'remote': {'type': 'generic',
    #         'url': 'https://git.musl-libc.org/cgit/musl/snapshot/v1.2.2.tar.gz'}}
    #

    # Different repos have different repository states
    for repo in sbom['metadata']['aggregator']['alpine']['aports']['repo']:
        # There might be repos with no packages
        if 'source' in sbom['metadata']['aggregator']['alpine']['aports']['repo'][repo]:
            source = sbom['metadata']['aggregator']['alpine']['aports']['repo'][repo]['source']
            hash = sbom['metadata']['aggregator']['alpine']['aports']['repo'][repo]['hash']
            git_manager.checkout(hash, "%s/%s" % (srcdir, ALPINE_REPO_NAME))

            # Iterate through all packages
            for package in source:
                index = package['index']
                if 'aggregate' in sbom['dependencies'][index] and 'source' in sbom['dependencies'][index][
                        'aggregate'] and 'external' in sbom['dependencies'][index]['aggregate']['source']:
                    src = sbom['dependencies'][index]['aggregate']['source']['external']
                    if src_type in ['all', 'code']:
                        for code in src['code']:
                            if 'generic' in code['remote']['type']:
                                path = code['local']['path']
                                url = code['remote']['url']
                                dstpath = dstdir + "/" + path
                                directory = os.path.dirname(dstpath)
                                dirpath = Path(directory)
                                dirpath.mkdir(parents=True, exist_ok=True)
                                try:
                                    file = req.get(url, allow_redirects=True)
                                    open(dstpath, 'wb').write(file.content)
                                except BaseException:
                                    sys.stderr.write(
                                        "    **********Problem to download [%s] from [%s]\n" %
                                        (package['package'], url))
                                else:
                                    if debug:
                                        sys.stdout.write(
                                            "External code downloaded: %s\n" % url)
                    if src_type in ['all', 'patch']:
                        for code in src['patch']:
                            if 'generic' in code['remote']['type']:
                                path = code['local']['path']
                                url = code['remote']['url']
                                dstpath = dstdir + "/" + path
                                directory = os.path.dirname(dstpath)
                                dirpath = Path(directory)
                                dirpath.mkdir(parents=True, exist_ok=True)
                                try:
                                    file = req.get(url, allow_redirects=True)
                                    open(dstpath, 'wb').write(file.content)
                                except BaseException:
                                    sys.stderr.write(
                                        "    **********Problem to download [%s] from [%s]\n" %
                                        (package['package'], url))
                                else:
                                    if debug:
                                        sys.stdout.write(
                                            "External patch downloaded: %s\n" % url)


def create_commit_map(resolved_sbom):
    """
       Arrange packages by repository ( main, community )
       Exclude sub-packages, since they share APKBUILD
    """
    packages_commit = {}
    if 'dependencies' in resolved_sbom:
        i = 0
        for package in resolved_sbom['dependencies']:
            parent = package['pipeline']['aggregator']['alpine']['parent']
            repo = package['pipeline']['aggregator']['alpine']['repo']
            ID = package['ID']
            entry = {}
            entry['ID'] = ID
            entry['index'] = i
            product = package['pipeline']['product']
            entry['package'] = product
            if parent == product:
                if repo not in packages_commit:
                    packages_commit[repo] = []
                    packages_commit[repo].append(entry)
                else:
                    packages_commit[repo].append(entry)
            i = i + 1

    if 'metadata' in resolved_sbom:
        for repo in resolved_sbom['metadata']['aggregator']['alpine']['aports']['repo']:
            if repo in packages_commit:
                resolved_sbom['metadata']['aggregator']['alpine']['aports']['repo'][repo]['source'] = packages_commit[repo]
    return resolved_sbom


def main():

    args = parse_cmdline()
    mode = "internal"
    src_type = "all"

    if args.pull:
        git_manager.pull("%s/%s" % (args.src, ALPINE_REPO_NAME))

    if args.mode:
        if args.mode in ['internal', 'external', 'all']:
            mode = args.mode
        else:
            sys.stderr.write("mode value is wrong\n")
            sys.exit(1)

    if args.type:
        if args.type in ['build', 'code', 'patch', 'all']:
            src_type = args.type
        else:
            sys.stderr.write("type value is wrong\n")
            sys.exit(1)

    if args.resolved:
        resolved_sbom = import_json(args.resolved)
        try:
            tag = resolved_sbom["metadata"]["aggregator"]["alpine"]["aports"]["repo"]["main"]["tag"]
            arch = resolved_sbom["metadata"]["aggregator"]["alpine"]["aports"]["arch"]
        except BaseException:
            sys.stderr.write(
                "Unable to find tag and architecture in main repo for SBOM %s\n" %
                args.resolved)
            sys.exit(1)
        else:
            resolved_sbom = create_commit_map(resolved_sbom)

    if args.debug:
        sys.stdout.write("mode: [internal|external|all]: %s\n" % mode)
        sys.stdout.write("type: [code|patch|build|all]:  %s\n" % src_type)
        sys.stdout.write("tag: %s\n" % tag)

    dstdir = args.output + "/" + tag + "." + arch
    path = Path(dstdir)
    path.mkdir(parents=True, exist_ok=True)

    if mode in ['all']:
        if args.debug:
           sys.stdout.write("mode: all\n")
        get_internal_code(
            resolved_sbom,
            args.src,
            dstdir,
            mode,
            src_type,
            args.debug)
        get_external_code(
            resolved_sbom,
            args.src,
            dstdir,
            mode,
            src_type,
            args.debug)
    elif mode in ['internal']:
        if args.debug:
           sys.stdout.write("mode: internal\n")
        get_internal_code(
            resolved_sbom,
            args.src,
            dstdir,
            mode,
            src_type,
            args.debug)
    elif mode in ['external']:
        if args.debug:
           sys.stdout.write("mode: external\n")
        get_external_code(
            resolved_sbom,
            args.src,
            dstdir,
            mode,
            src_type,
            args.debug)
    sys.exit(0)


if __name__ == '__main__':
    sys.exit(main())

import sys
import os
import re

import pprint
import argparse
import json
import glob
import tempfile
import subprocess
import fnmatch
import hashlib

from copy import deepcopy
import tempfile


try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO
import shutil


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
        default=None)
    y = io.getvalue()
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

def parse_dep(ind, index, debug): 
    temp = {}


    dep = index[ind]['struct_raw']


    if 'depend' in dep: 
     tmp = {}
     tmp['develop'] = [] 
     tmp['execute'] = [] 
     tmp['file'] = [] 
     tmp['package'] = [] 
     deps = ' '.join(dep['depend']) 
     for s in deps.split(): 
      if re.match(r'^so:.*', s):
        if re.match(r'^so:.*=.*', s):
           tmp['develop'].append(s[3:].split('=')[0]) 
        else: 
           tmp['develop'].append(s[3:]) 
      elif re.match(r'^cmd:.*', s):
        tmp['execute'].append(s[4:])
      elif re.match(r'^pc:.*', s):
        pass
      else: 
        if re.match(r'.*=.*', s):
          key = s.split('=')[0]
          if key in index: 
             if 'parent'  in index[key] and key == index[key]['parent']: 
               tmp['package'].append(key)
          else: 
             tmp['file'].append(key)
        else: 
          if s in index: 
             if 'parent'  in index[s] and s == index[s]['parent']: 
                tmp['package'].append(s)
          else: 
             tmp['file'].append(s)
     temp['depend'] = tmp 

    if 'provide' in dep: 
     tmp = {}
     tmp['develop'] = [] 
     tmp['execute'] = [] 
     tmp['file'] = [] 
     deps = ' '.join(dep['provide']) 
     for s in deps.split(): 
      if re.match(r'^so:.*', s):
        if re.match(r'^so:.*=.*', s):
           tmp['develop'].append(s[3:].split('=')[0]) 
        else: 
           tmp['develop'].append(s[3:]) 
      elif re.match(r'^cmd:.*', s):
        cmd_tmp = s[4:]
        key = cmd_tmp.split('=')[0]
        #if debug: 
        #   print(key) 
        #tmp['execute'].append(s[4:])
        tmp['execute'].append(key)
      elif re.match(r'^pc:.*', s):
        pass
      else: 
        if re.match(r'.*=.*', s):
          key = s.split('=')[0]
          tmp['file'].append(key)
        else: 
          tmp['file'].append(s)
     temp['provide'] = tmp 
     #if debug: 
     #  print(temp['provide']) 

    return temp
    return deepcopy(temp)




def parse_apkindex(buffer, debug):
    apkindex = {}
    pkgname = ""
    temp = {}
    inconsistent = []
    temp['childs'] = []
    dependencies = {} 
    dependencies['install'] = [] 
    dependencies['provide'] = [] 
    dependencies['depend'] = [] 
    
    for line in buffer.split('\n'):
        if len(line) > 2:
            if line[0] == 'P':
                pkgname = line[2:]
            elif line[0] == 'V':
                temp['pkgver'] = line[2:].split('-')[0]
                temp['pkgrel'] = line[2:].split('-')[1].replace('r', '')
            elif line[0] == 'o':
                tmp = line[2:].split()
                if len(tmp) == 1:
                    temp['parent'] = line[2:]
                elif len(tmp) > 1:
                    temp['parent'] = tmp[0]
                    temp['parents'] = line[2:]
            elif line[0] == 'c':
                temp['commit'] = line[2:]
            elif line[0] == 'A':
                temp['arch'] = line[2:]
            elif line[0] == 'D':
                dependencies['depend'].append(line[2:])
            elif line[0] == 'p':
                dependencies['provide'].append(line[2:])
            elif line[0] == 'i':
                dependencies['install'].append(line[2:])
        else:
            if pkgname != "":
                # End of package definition, assure that all fields exists
                if 'pkgver' in temp and 'pkgrel' in temp and 'parent' in temp and 'commit' in temp:
                    temp['struct_raw'] = dependencies
                    apkindex[pkgname] = temp
                else:
                    inconsistent.append(pkgname)
                pkgname = ""
                temp = {}
                temp['childs'] = []
                dependencies = {} 
                dependencies['install'] = [] 
                dependencies['provide'] = [] 
                dependencies['depend'] = [] 

    # Create list of childrens
    for pkg in apkindex:
        if 'parent' in apkindex[pkg]:
            parent = apkindex[pkg]['parent']
            if pkg != parent:
                apkindex[parent]['childs'].append(pkg)

    result = {}
    result['apkindex'] = apkindex
    result['inconsistent'] = inconsistent
    return result


def parse_description(buffer):
    result = {}
    result['raw'] = buffer
    try:
        tag = buffer.split('-')[0]
        result['tag'] = tag
        bn = buffer.split('-')[1]
        result['build-number'] = bn
        commit_hash = buffer.split('-')[2]
        result['hash'] = commit_hash[1:]
    except BaseException:
        pass
    return result


def unpack_embedded_tarballs(root_dir):
    result = {}
    CWD = os.getcwd()
    for filename in glob.iglob(root_dir + '**/**', recursive=True):
        comp = filename.split('/')
        if 'APKINDEX.tar.gz' in comp:
            cmd = "tar xzf %s" % filename
            os.chdir(os.path.dirname(filename))
            tmp = run(cmd)
            os.chdir(CWD)

    return result


def create_index(result, debug):
    if 'apkindex' in result:
        if len(result['apkindex']) != 1:
            tmp = {}
            tmp['status'] = 'error'
            tmp['info'] = 'It seems that is a mix of APKINDEX files from different versions, clean the directory of downloaded APKINDEX:tar.gz'
            tmp['debug'] = list(result['apkindex'].keys())
            return tmp

        index = {}
        for tag in result['apkindex']:
            for repo in result['apkindex'][tag]:
                for comp in result['apkindex'][tag][repo]["APKINDEX"]:
                    entry = result['apkindex'][tag][repo]["APKINDEX"][comp]
                    entry['repo'] = repo
                    entry['tag'] = tag
                    index[comp] = entry
        provide_dict = {} 
        provide_dict['develop'] = {} 
        provide_dict['execute'] = {} 

        for ind in index: 
          temp = parse_dep(ind, index, debug)

          if 'provide' in temp and 'develop' in temp['provide']: 
            for lib in temp['provide']['develop']: 
              if lib not in provide_dict['develop'] and 'parent' in index[ind]: 
                 provide_entry  = {} 
                 provide_entry['parent'] = index[ind]['parent'] 
                 if ind != index[ind]['parent']: 
                    provide_entry['child'] = ind
                 provide_dict['develop'][lib] = provide_entry

          if 'provide' in temp and 'execute' in temp['provide']: 
            for lib in temp['provide']['execute']: 
              if lib not in provide_dict['execute'] and 'parent' in index[ind]: 
                 provide_entry  = {}
                 provide_entry['parent'] = index[ind]['parent']
                 if ind != index[ind]['parent']: 
                    provide_entry['child'] = ind
                 provide_dict['execute'][lib] = provide_entry


        for ind in index: 
          temp = parse_dep(ind, index, debug)
          temp_struct = {}  
          temp_struct['develop'] = {}  
          temp_struct['execute'] = {}  
          temp_struct['package'] = {}  

          if 'depend' in temp and 'package' in temp['depend']: 
             temp_struct['package']= temp['depend']['package']
             
          if 'depend' in temp and 'develop' in temp['depend']: 
            for lib in temp['depend']['develop']: 
              if lib in provide_dict['develop']: 
                 temp_struct['develop'][lib] = provide_dict['develop'][lib] 
             
          if 'depend' in temp and 'execute' in temp['depend']: 
            for lib in temp['depend']['execute']: 
              if lib in provide_dict['execute']: 
                 temp_struct['execute'][lib] = provide_dict['execute'][lib] 
            
          index[ind]['depends'] = temp_struct
          
    result['index'] = index
    result['provide'] = provide_dict 
    return result


def commit_map(result):
    packages_commit = {}
    if 'index' in result:
        for package in result['index']:
            if 'parent' in result['index'][package] and package == result['index'][package]['parent']:
                commit = result['index'][package]['commit']
                if commit in packages_commit:
                    packages_commit[commit].append(package)
                else:
                    packages_commit[commit] = []
                    packages_commit[commit].append(package)

    result['commit_map'] = packages_commit
    return result


def process_tarball(tarball, debug, create_commit_map=False):
    dirpath = tempfile.mkdtemp()
    CWD = os.getcwd()
    os.chdir(dirpath)
    tarballpath = "%s/%s" % (dirpath, "apkindex.tar")

    fp = open(tarballpath, "wb")
    fp.write(tarball)
    fp.close()
    cmd = "tar xf %s" % tarballpath
    try:
        hash_object = hashlib.md5(tarball)
        hex_dig = hash_object.hexdigest()
    except BaseException:
        hex_dig = "failed_to_calculate_hash"

    tmp = run(cmd)
    unpack_embedded_tarballs(dirpath)
    result = {}
    result['status'] = 'ok'
    result['repos'] = {}
    result['aggregator'] = 'alpine'
    result['hash'] = hex_dig
    result['apkindex'] = {}
    for filename in glob.iglob(dirpath + '**/**', recursive=True):
        comp = filename.split('/')
        if 'APKINDEX' in comp:
            repo = comp[5]
            tag = comp[4]
            arch = comp[6]
            try:
                fp = open(filename, "r")
                APKINDEX = fp.read()
                fp.close()
            except BaseException:
                result['status'] = 'error'
            else:
                if tag not in result['apkindex']:
                    result['apkindex'][tag] = {}
                if repo not in result['apkindex'][tag]:
                    result['apkindex'][tag][repo] = {}

                temp = parse_apkindex(APKINDEX, debug)
                result['apkindex'][tag][repo]['APKINDEX'] = temp['apkindex']
                result['apkindex'][tag][repo]['inconsistent'] = temp['inconsistent']
                result['apkindex'][tag][repo]['arch'] = arch

        if 'DESCRIPTION' in comp:
            repo = comp[5]
            tag = comp[4]
            arch = comp[6]
            try:
                fp = open(filename, "r")
                DESCRIPTION = fp.read()
                fp.close()
            except BaseException:
                result['status'] = 'error'
            else:
                if tag not in result['apkindex']:
                    result['apkindex'][tag] = {}
                if repo not in result['apkindex'][tag]:
                    result['apkindex'][tag][repo] = {}

                result['apkindex'][tag][repo]['DESCRIPTION'] = parse_description(
                    DESCRIPTION)
                result['repos'][repo] = parse_description(DESCRIPTION)
    os.chdir(CWD)
    shutil.rmtree(dirpath)

    result = create_index(result, debug)
    if create_commit_map == True:
        result = commit_map(result)
    return result


def process_desired_bom(os_bom):

    tmp = []
    for line in os_bom.split('\n'):
        fields = line.split()
        nr_of_fields = len(fields)
        if nr_of_fields > 1 and fields[nr_of_fields -
                                       1][0] == "#" and fields[nr_of_fields - 1][1] == "S":
            strategic_component = fields[0]
            if strategic_component not in tmp:
                tmp.append(strategic_component)
    return tmp


def process_config(config):

    tmp = {}
    for line in config.split('\n'):
        fld = line.split("=")
        if len(fld) == 2:
            tmp[fld[0]] = fld[1].replace('"', "")
    return tmp


def process_resolved_bom(os_bom):
    # ['a', 'alpinelinux', 'openjdk8-jre-base', '8.151.12', 'r0', 'alpine_linux_3.7', 'http://icedtea.classpath.org/']

    NR_OF_CPE_FIELDS = 7
    tmp = {}
    tmp['tools'] = {}
    tmp['dist'] = {}
    syntax = {}
    syntax['rejected'] = []
    for line in os_bom.split('\n'):
        fields = line.split(',')
        if len(fields) == NR_OF_CPE_FIELDS:
            if fields[0] == 'a':
                vendor = fields[1].lstrip()
                product = fields[2].lstrip()
                version = fields[3].lstrip()
                patch = fields[4].lstrip()
                platform = fields[5].lstrip()
                weblink = fields[6].lstrip()

                if vendor not in tmp['dist']:
                    tmp['dist'][vendor] = {}
                if product not in tmp['dist'][vendor]:
                    tmp['dist'][vendor][product] = {}
                if version not in tmp['dist'][vendor][product]:
                    tmp['dist'][vendor][product][version] = {}
                if patch not in tmp['dist'][vendor][product][version]:
                    tmp['dist'][vendor][product][version][patch] = {}
                if platform not in tmp['dist'][vendor][product][version][patch]:
                    tmp['dist'][vendor][product][version][patch][platform] = {}
                    tmp['dist'][vendor][product][version][patch][platform]['weblink'] = weblink

            else:
                syntax['rejected'].append("CPE must start with a: [%s]" % line)
        elif line != "":
            syntax['rejected'].append(
                "Expect %d fields separated by , [%s]" % (NR_OF_CPE_FIELDS, line))
    return tmp, syntax


def format_dep(bom, metadata, desired, settings, debug):

    if 'apkindex' in metadata:
        apk_match = {}
        apk_match['lookup'] = {}
        apk_match['structure'] = {}
        apk_match['lookup']['total'] = 0
        apk_match['lookup']['miss'] = 0
        apk_match['lookup']['match'] = 0
        apk_match['structure']['childs'] = 0
        apk_match['structure']['parents'] = 0
    adp_out = {}
    adp_out['dependencies'] = []
    adp_out['modelVersion'] = "1.1"
    for vendor in bom['dist']:
        for product in bom['dist'][vendor]:
            for version in bom['dist'][vendor][product]:
                for patch in bom['dist'][vendor][product][version]:
                    for platform in bom['dist'][vendor][product][version][patch]:
                        weblink = str(bom['dist'][vendor][product]
                                      [version][patch][platform]['weblink'])
                        s_product = str(product)
                        s_version = str(version)
                        s_vendor = str(vendor)
                        s_patch = str(patch)
                        s_platform = str(platform)
                        idx = "native-%s-%s-%s-%s-%s" % (
                            s_product, s_version, s_patch, s_vendor, s_platform)
                        mapper = {}
                        mapper['category'] = 'FOSS'
                        if product in desired:
                            mapper['strategic'] = True
                        else:
                            mapper['strategic'] = False
                        temp = {}
                        temp['domain'] = 'linux'
                        temp['product'] = s_product
                        temp['target_sw'] = s_platform
                        temp['vendor'] = s_vendor
                        temp['version'] = s_version
                        temp['update'] = s_patch
                        if 'apkindex' in metadata and s_patch[0] == 'r':
                            temp['pkgrel'] = s_patch[1:]
                        temp['web_url'] = weblink
                        if 'apkindex' in metadata and 'index' in metadata:
                            apk_match['lookup']['total'] += 1
                            temp['aggregator'] = {}
                            temp['aggregator']['type'] = 'alpine'
                            if s_product in metadata['index'] and s_version in metadata['index'][s_product]['pkgver']:
                                apk_match['lookup']['match'] += 1
                                temp['aggregator']['match'] = True
                                temp['aggregator']['alpine'] = metadata['index'][s_product]
                                if s_product != metadata['index'][s_product]['parent']:
                                    apk_match['structure']['childs'] += 1
                                else:
                                    apk_match['structure']['parents'] += 1

                            else:
                                temp['aggregator']['match'] = False
                                apk_match['lookup']['miss'] += 1

                        node = {}
                        node['ID'] = idx
                        node['pipeline'] = temp
                        node['mapper'] = mapper
                        #if debug: 
                        #   pprint.pprint(node) 
                        adp_out['dependencies'].append(node)

    if 'apkindex' in metadata:
        tag = list(metadata['apkindex'].keys())[0]
        apk_dict = {}
        apk_dict['repo'] = {}
        for repo in metadata['apkindex'][tag]:
            apk_dict['arch'] = metadata['apkindex'][tag][repo]['arch']
            apk_dict['repo'][repo] = metadata['apkindex'][tag][repo]['DESCRIPTION']
        adp_out['metadata'] = {}
        adp_out['metadata']['aggregator'] = {}
        adp_out['metadata']['aggregator']['alpine'] = {}
        if 'hash' in metadata:
            adp_out['metadata']['aggregator']['alpine']['apkindex'] = {}
            adp_out['metadata']['aggregator']['alpine']['apkindex']['hash'] = metadata['hash']
        adp_out['metadata']['aggregator']['alpine']['settings'] = settings
        adp_out['metadata']['aggregator']['alpine']['aports'] = apk_dict
        adp_out['metadata']['aggregator']['alpine']['stats'] = apk_match
    return adp_out


args_options = {'opt': [{'long': '--debug',
                         'help': 'Debug mode'},
                        {'long': '--index',
                         'help': 'Coordinate all packages that share the same commit state'}
                        ],
                'opt_w_arg': [
    {'long': '--pkgindex',
     'help': 'path to APKINDEX.tar.gz',
     'meta': 'pkgindex',
     'required': True},
    {'long': '--desired',
     'help': 'path to desired SBOM for Alpine',
     'meta': 'desired',
     'required': False},
    {'long': '--config',
     'help': 'path to build configuration Alpine base OS',
     'meta': 'config',
     'required': False},
    {'long': '--resolved',
     'help': 'path to resolved SBOM for Alpine',
     'meta': 'resolved',
     'required': False},
    {'long': '--output',
     'help': 'Output directory ',
     'meta': 'output',
     'required': False},
]}


def parse_cmdline():
    """ Parse command-line and return args """
    parser = argparse.ArgumentParser(
        description='Collect build information ' +
        'together with commit information' +
        'Maps relation in JSON.')

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

    debug = args.debug

    if args.pkgindex:
        fp = open(args.pkgindex, "rb")
        buf = fp.read()
        fp.close()
        try:
            fp = open(args.pkgindex, "rb")
            buf = fp.read()
            fp.close()
            if args.index:
                alpine_apk_index = process_tarball(buf, debug, create_commit_map=True)
            else:
                alpine_apk_index = process_tarball(buf, debug)
        except BaseException:
            sys.stderr.write("Error processing %s\n" % args.pkgindex)
            sys.exit(1)
        if args.desired is None and args.resolved is None and args.output:
            json = export_json(alpine_apk_index)
            fp = open(args.output, "w")
            fp.write(json)
            fp.close()

    if args.desired:
        try:
            fp = open(args.desired, "r")
            buf = fp.read()
            fp.close()
            desired = process_desired_bom(buf)
        except BaseException:
            sys.stderr.write("Error processing %s\n" % args.desired)
            sys.exit(1)

    if args.config:
        fp = open(args.config, "r")
        buf = fp.read()
        fp.close()
        settings = process_config(buf)
        try:
            fp = open(args.config, "r")
            buf = fp.read()
            fp.close()
            settings = process_config(buf)
        except BaseException:
            sys.stderr.write("Error processing %s\n" % args.config)
            sys.exit(1)

    if args.resolved:
        try:
            fp = open(args.resolved, "r")
            buf = fp.read()
            fp.close()
            resolved, stats = process_resolved_bom(buf)
        except BaseException:
            sys.stderr.write("Error processing %s\n" % args.resolved)
            sys.exit(1)

    if args.output and args.resolved and args.desired and args.config:
        json = export_json(
            format_dep(
                resolved,
                alpine_apk_index,
                desired,
                settings, debug))
        try:
            fp = open(args.output, "w")
            fp.write(json)
            fp.close()
        except BaseException:
            sys.stderr.write("Cannot open %s" % args.output)
            sys.exit(1)

    return 0


if __name__ == '__main__':
    sys.exit(main())

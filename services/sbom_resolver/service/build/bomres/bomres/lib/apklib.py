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

import bomres.lib.git_manager as git_manager




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


def handle_double_colon(string):
    tmp = string.split('::')
    result = {}
    result['remote'] = ""
    result['local'] = ""
    if len(tmp) > 1:
        result['remote'] = tmp[1]
        result['local'] = tmp[0]
        return result
    else:
        tmp = string.split('/')
        index = len(tmp)
        if index > 1:
            result['remote'] = string
            result['local'] = tmp[index - 1]
        else:
            result['remote'] = string
            result['local'] = string
        return result


def parse_apkbuild_manifest(name, repository, path, repo_hash_dict, apkbuild, repolink):

    
    """
Change state machine to include install scripts for openldap 2022-04-05
opendlap

install="
        $pkgname.pre-install
        $pkgname.post-install
        $pkgname.pre-upgrade
        $pkgname.post-upgrade
        $pkgname-lloadd.pre-install
        "
    """

    parse_info = {}
    result = {}
    result['repository'] = repository

    result['source'] = []
    result['checkdepends'] = []
    result['makedepends'] = []
    result['repolink'] = repolink

    STATE_SRC = False
    START_SRC = 'source="'

    STATE_INSTALL = False
    START_INSTALL = 'install="'

    START_SHA512 = 'sha512sums="'
    STATE_SHA512 = False

    START_SHA256 = 'sha256sums="'
    STATE_SHA256 = False

    START_MD5 = 'md5sums="'
    STATE_MD5 = False

    START_SECFIXES = "# secfixes:"
    STATE_SECFIXES = False

    START_SUBPACK = 'subpackages="'
    STATE_SUBPACK = False

    START_DEPCHECK = 'checkdepends="'
    STATE_DEPCHECK = False

    START_MAKECHECK = 'makedepends="'
    STATE_MAKECHECK = False

    START_DEVCHECK = 'depends_dev="'
    STATE_DEVCHECK = False


    #
    #  Open APKBUILD and process line by line in state machine
    #
    # print("Processing %s" % name )
    try:
        fp = open(path)
        buff = fp.read()
        fp.close()
    except BaseException:
        parse_info = {}
        parse_info['system'] = {}
        parse_info['system']['error'] = "Unable to open %s" % path
        return result, parse_info

    var_map = {}
    # See issue https://github.com/Nordix/bomres/issues/48
    prevent_version_truncation_list = [] 

    for s in buff.split('\n'):

        if re.findall(r'^pkgname=.*?$', s):
            v = s.split('=')[1].strip('"')
            k = 'pkgname'
            # See APKBUILD for gcc in repo main, multiple definitions
            if 'pkgname' not in result:
                result[k] = v
                var_map[k] = v

        elif re.findall(r'^pkgver=.*?$', s):
            v = s.split('=')[1].strip('"')
            k = 'pkgver'
            result[k] = v
            var_map[k] = v
            major_minor_maint = v.split('.')
            if len(major_minor_maint) > 2:
               _v = '.'.join(major_minor_maint[:-1])
               if name not in prevent_version_truncation_list: 
                  var_map['_v'] = _v

        elif re.findall(r'^pkgrel=.*?$', s):
            result['pkgrel'] = s.split('=')[1].strip('"')

        elif re.findall(r'^url=.*?$', s):
            result['url'] = s.split('=')[1].strip('"')

        elif re.findall(r'^arch=.*?$', s):
            tmp = s.split('=')[1]
            tmp = tmp.split("#")[0]
            tmp = tmp.replace('"', '')
            tmp = tmp.rstrip()
            tmp = tmp.lstrip()
            result['arch'] = tmp

        elif re.findall(r'^license=.*?$', s):
            result['license'] = s.split('=')[1].strip('"')

        elif re.findall(r'^depends=.*?$', s):
            result['depends'] = s.split('=')[1].strip('"')


        elif re.findall(r'^triggers=.*?$', s):
            trigger = s.split('=')[1].strip('"')
            tmp = handle_double_colon(trigger)
            if tmp not in result['source']:
               if 'source' not in result: 
                  result['source'] = [] 
               result['source'].append(tmp)


        #  https://wiki.archlinux.org/title/GNOME_package_guidelines
        #  openssl _abiver=${pkgver%.*}   1.1.1k -> 1.1

        #
        # If keyword not listed above, it end up here 
        # 
        elif re.findall(r'^[_a-zA-Z].*=["${}.%a-zA-Z0-9].*', s):
        
            k = s.split('=')[0]
            v = s.split('=')[1]
            v = v.replace('"', '')
            v = v.replace('{', '')
            v = v.replace('}', '')
            # assignment in code , see gcc in main repo
            if not re.search('[ \t]+', k):
               var_map[k] = v

        #
        # Extract subpackages dependency from APKBUILD
        # Line starts with subpackages=" and ends with "
        # Could span multiple lines
        # SUBPACKAGE:WHERE_TO_COPY sfdisk:_mv_bin , need to strip based on : (
        # util-linux )
        if (STATE_SUBPACK):
            # This entry handles entries after start and before end
            tmp = s.lstrip()
            tmp = tmp.strip('"')
            if tmp != "":
                for i in tmp.split():
                    ii = i.split(':')[0]
                    result['subpackages'].append(ii)

        if (s.startswith(START_SUBPACK) and s.endswith('"')):
            # One line
            result['subpackages'] = []
            tmp = s.split(START_SUBPACK)[1]
            tmp = tmp.lstrip()
            tmp = tmp.rstrip('"')
            if tmp != "":
                for i in tmp.split():
                    ii = i.split(':')[0]
                    result['subpackages'].append(ii)

        elif (s.startswith(START_SUBPACK)):
            # multiline
            STATE_SUBPACK = True
            result['subpackages'] = []
            tmp = s.split(START_SUBPACK)[1]
            tmp = tmp.lstrip()
            if tmp != "":
                for i in tmp.split():
                    ii = i.split(':')[0]
                    result['subpackages'].append(ii)

        if (STATE_SUBPACK and s.endswith('"')):
            # End of multiline source section
            STATE_SUBPACK = False
            tmp = s.lstrip()
            tmp = tmp.strip('"')
            if tmp != "":
                for i in tmp.split():
                    ii = i.split(':')[0]
                    result['subpackages'].append(ii)

        if (STATE_INSTALL):
            # This entry handles entries after start and before end
            tmp = s.lstrip()
            tmp = tmp.strip('"')
            for fi in tmp.split():  
              if len(fi) > 0:
                temp = handle_double_colon(fi)
                if temp not in result['source']:
                    result['source'].append(temp)

        if (s.startswith(START_INSTALL) and s.endswith('"')):
            # One line
            STATE_INSTALL = True
            tmp = s.split(START_INSTALL)[1]
            tmp = tmp.lstrip()
            tmp = tmp.rstrip('"')
            for fi in tmp.split():  
              if len(fi) > 0:
                STATE_INSTALL = False
                temp = handle_double_colon(fi)
                if temp not in result['source']:
                    result['source'].append(temp)

        elif (s.startswith(START_INSTALL)):
            # multiline
            STATE_INSTALL = True
            tmp = s.split(START_INSTALL)[1]
            tmp = tmp.lstrip()
            tmp = tmp.rstrip('"')
            for fi in tmp.split():  
              if len(fi) > 0:
                temp = handle_double_colon(fi)
                if temp not in result['source']:
                    result['source'].append(temp)

        elif (STATE_INSTALL and s.endswith('"')):
            # End of multiline source section
            STATE_INSTALL = False
            if s.startswith(START_INSTALL): 
              tmp = s.split(START_INSTALL)[1]
              tmp = tmp.lstrip()
            else: 
              tmp = s.lstrip()
            tmp = tmp.strip('"')
            for fi in tmp.split():  
              if len(fi) > 0:
                temp = handle_double_colon(fi)
                if temp not in result['source']:
                    result['source'].append(temp)

        #
        # Extract source code dependency from APKBUILD
        # Line starts with source=" and ends with "
        # Could span multiple lines
        #
        if (STATE_SRC):
            # This entry handles entries after start and before end
            tmp = s.lstrip()
            tmp = tmp.strip('"')
            for fi in tmp.split():  
              if len(fi) > 0:
                temp = handle_double_colon(fi)
                if temp not in result['source']:
                    result['source'].append(temp)

        if (s.startswith(START_SRC) and s.endswith('"')):
            # One line
            if 'source' not in result: 
               result['source'] = []
            tmp = s.split(START_SRC)[1]
            tmp = tmp.lstrip()
            tmp = tmp.rstrip('"')
            for fi in tmp.split():  
              if len(fi) > 0:
                temp = handle_double_colon(fi)
                if temp not in result['source']:
                    result['source'].append(temp)

        elif (s.startswith(START_SRC)):
            # multiline
            STATE_SRC = True
            tmp = s.split(START_SRC)[1]
            tmp = tmp.lstrip()
            tmp = tmp.rstrip('"')
            for fi in tmp.split():  
              if len(fi) > 0:
                temp = handle_double_colon(fi)
                if temp not in result['source']:
                    result['source'].append(temp)

        if (STATE_SRC and s.endswith('"')):
            # End of multiline source section
            STATE_SRC = False
            tmp = s.lstrip()
            tmp = tmp.strip('"')
            for fi in tmp.split():  
              if len(fi) > 0:
                temp = handle_double_colon(fi)
                if temp not in result['source']:
                    result['source'].append(temp)

        if (STATE_DEPCHECK):
            # This entry handles entries after start and before end
            tmp = s.lstrip()
            tmp = tmp.strip('"')
            for fi in tmp.split():  
              if len(fi) > 0:
                if fi not in result['checkdepends']:
                   result['checkdepends'].append(fi)

        if (s.startswith(START_DEPCHECK) and s.endswith('"')):
            # One line
            tmp = s.split(START_DEPCHECK)[1]
            tmp = tmp.lstrip()
            tmp = tmp.rstrip('"')
            STATE_DEPCHECK = True
            for fi in tmp.split():  
              if len(fi) > 0:
                STATE_DEPCHECK = False
                if fi not in result['checkdepends']:
                   result['checkdepends'].append(fi)

        elif (s.startswith(START_DEPCHECK)):
            # multiline
            STATE_DEPCHECK = True
            tmp = s.split(START_DEPCHECK)[1]
            tmp = tmp.lstrip()
            tmp = tmp.rstrip('"')
            for fi in tmp.split():  
              if len(fi) > 0:
                if fi not in result['checkdepends']:
                   result['checkdepends'].append(fi)

        if (STATE_DEPCHECK and s.endswith('"')):
            # End of multiline checkdepends section
            tmp = s.lstrip()
            if not s.startswith(START_DEPCHECK): 
               STATE_DEPCHECK = False
            else: 
               tmp = tmp.split(START_DEPCHECK)[1]
            tmp = tmp.strip('"')
            for fi in tmp.split():  
              if len(fi) > 0:
                temp = fi
                if temp not in result['checkdepends']:
                   result['checkdepends'].append(temp)



        if (STATE_DEVCHECK):
            # This entry handles entries after start and before end
            tmp = s.lstrip()
            tmp = tmp.strip('"')
            for fi in tmp.split():  
              if len(fi) > 0:
                if fi not in result['makedepends']:
                   result['makedepends'].append(fi)

        if (s.startswith(START_DEVCHECK) and s.endswith('"')):
            # One line
            tmp = s.split(START_DEVCHECK)[1]
            tmp = tmp.lstrip()
            tmp = tmp.rstrip('"')
            # makedepends="" 
            if not s.endswith('""'): 
              STATE_DEVCHECK = True
            for fi in tmp.split():  
              if len(fi) > 0:
                STATE_DEVCHECK = False
                if fi not in result['makedepends']:
                   result['makedepends'].append(fi)

        elif (s.startswith(START_DEVCHECK)):
            # multiline
            STATE_DEVCHECK = True
            tmp = s.split(START_DEVCHECK)[1]
            tmp = tmp.lstrip()
            tmp = tmp.rstrip('"')
            for fi in tmp.split():  
              if len(fi) > 0:
                if fi not in result['makedepends']:
                   result['makedepends'].append(fi)

        if (STATE_DEVCHECK and s.endswith('"')):
            # End of multiline makedepends section
            tmp = s.lstrip()
            if not s.startswith(START_DEVCHECK): 
               STATE_DEVCHECK = False
            else: 
               tmp = tmp.split(START_DEVCHECK)[1]
            tmp = tmp.strip('"')
            for fi in tmp.split():  
              if len(fi) > 0:
                temp = fi
                if temp not in result['makedepends']:
                   result['makedepends'].append(temp)


        if (STATE_MAKECHECK):
            # This entry handles entries after start and before end
            tmp = s.lstrip()
            tmp = tmp.strip('"')
            for fi in tmp.split():  
              temp = fi.rstrip('<')
              temp = temp.rstrip('>')
              if len(temp) > 0:
                if temp not in result['makedepends']:
                   result['makedepends'].append(temp)

        if (s.startswith(START_MAKECHECK) and s.endswith('"')):
            # One line
            tmp = s.split(START_MAKECHECK)[1]
            tmp = tmp.lstrip()
            tmp = tmp.rstrip('"')
            # makedepends="" 
            if not s.endswith('""'): 
              STATE_MAKECHECK = True
            for fi in tmp.split():  
              if re.findall(r'.*=.*', fi): 
                temp = fi.split('=')[0]
              else: 
                temp = fi
              temp = temp.rstrip('<')
              temp = temp.rstrip('>')
              if len(temp) > 0:
                STATE_MAKECHECK = False
                if temp not in result['makedepends']:
                   result['makedepends'].append(temp)

        elif (s.startswith(START_MAKECHECK)):
            # multiline
            STATE_MAKECHECK = True
            tmp = s.split(START_MAKECHECK)[1]
            tmp = tmp.lstrip()
            tmp = tmp.rstrip('"')
            for fi in tmp.split():  
              if re.findall(r'.*=.*', fi): 
                temp = fi.split('=')[0]
              else: 
                temp = fi
              temp = temp.rstrip('<')
              temp = temp.rstrip('>')
              if len(fi) > 0:
                if fi not in result['makedepends']:
                   result['makedepends'].append(fi)

        if (STATE_MAKECHECK and s.endswith('"')):
            # End of multiline makedepends section
            tmp = s.lstrip()
            if not s.startswith(START_MAKECHECK): 
               STATE_MAKECHECK = False
            else: 
               tmp = tmp.split(START_MAKECHECK)[1]
            tmp = tmp.strip('"')
            for fi in tmp.split():  
              if re.findall(r'.*=.*', fi): 
                temp = fi.split('=')[0]
              else: 
                temp = fi
              temp = fi.rstrip('<')
              temp = temp.rstrip('>')
              if len(temp) > 0:
                if temp not in result['makedepends']:
                   result['makedepends'].append(temp)
        #
        # Checksum
        # 

        if (STATE_MD5):
            tmp = s.lstrip()
            tmp = tmp.strip('"')
            tmp = tmp.split()
            if len(tmp) == 2:
                entry = {} 
                entry['type'] = 'md5' 
                entry['value'] = tmp[0] 
                result['checksum'][tmp[1]] = entry

        if (s.startswith(START_MD5) and s.endswith('"')):
            if 'checksum' not in result: 
            	result['checksum'] = {}
            tmp = s.split(START_MD5)[1]
            tmp = tmp.lstrip()
            tmp = tmp.rstrip('"')
            tmp = tmp.split()
            if len(tmp) == 2:
                entry = {} 
                entry['type'] = 'md5' 
                entry['value'] = tmp[0] 
                result['checksum'][tmp[1]] = entry

        elif (s.startswith(START_MD5)):
            STATE_MD5 = True
            if 'checksum' not in result: 
            	result['checksum'] = {}
            tmp = s.split(START_MD5)[1]
            tmp = tmp.lstrip()
            tmp = tmp.split()
            if len(tmp) == 2:
                entry = {} 
                entry['type'] = 'md5' 
                entry['value'] = tmp[0] 
                result['checksum'][tmp[1]] = entry

        if (STATE_MD5 and s.endswith('"')):
            STATE_MD5 = False
            tmp = s.lstrip()
            tmp = tmp.strip('"')
            tmp = tmp.split()
            if len(tmp) == 2:
                entry = {} 
                entry['type'] = 'md5' 
                entry['value'] = tmp[0] 
                result['checksum'][tmp[1]] = entry

        if (STATE_SHA256):
            tmp = s.lstrip()
            tmp = tmp.strip('"')
            tmp = tmp.split()
            if len(tmp) == 2:
                entry = {} 
                entry['type'] = 'sha256' 
                entry['value'] = tmp[0] 
                result['checksum'][tmp[1]] = entry

        if (s.startswith(START_SHA256) and s.endswith('"')):
            if 'checksum' not in result: 
            	result['checksum'] = {}
            tmp = s.split(START_SHA256)[1]
            tmp = tmp.lstrip()
            tmp = tmp.rstrip('"')
            tmp = tmp.split()
            if len(tmp) == 2:
                entry = {} 
                entry['type'] = 'sha256' 
                entry['value'] = tmp[0] 
                result['checksum'][tmp[1]] = entry

        elif (s.startswith(START_SHA256)):
            STATE_SHA256 = True
            if 'checksum' not in result: 
            	result['checksum'] = {}
            tmp = s.split(START_SHA256)[1]
            tmp = tmp.lstrip()
            tmp = tmp.split()
            if len(tmp) == 2:
                entry = {} 
                entry['type'] = 'sha256' 
                entry['value'] = tmp[0] 
                result['checksum'][tmp[1]] = entry

        if (STATE_SHA256 and s.endswith('"')):
            STATE_SHA256 = False
            tmp = s.lstrip()
            tmp = tmp.strip('"')
            tmp = tmp.split()
            if len(tmp) == 2:
                entry = {} 
                entry['type'] = 'sha256' 
                entry['value'] = tmp[0] 
                result['checksum'][tmp[1]] = entry

        if (STATE_SHA512):
            tmp = s.lstrip()
            tmp = tmp.strip('"')
            tmp = tmp.split()
            if len(tmp) == 2:
                entry = {} 
                entry['type'] = 'sha512' 
                entry['value'] = tmp[0] 
                result['checksum'][tmp[1]] = entry

        if (s.startswith(START_SHA512) and s.endswith('"')):
            if 'checksum' not in result: 
            	result['checksum'] = {}
            tmp = s.split(START_SHA512)[1]
            tmp = tmp.lstrip()
            tmp = tmp.rstrip('"')
            tmp = tmp.split()
            if len(tmp) == 2:
                entry = {} 
                entry['type'] = 'sha512' 
                entry['value'] = tmp[0] 
                result['checksum'][tmp[1]] = entry

        elif (s.startswith(START_SHA512)):
            STATE_SHA512 = True
            if 'checksum' not in result: 
            	result['checksum'] = {}
            tmp = s.split(START_SHA512)[1]
            tmp = tmp.lstrip()
            tmp = tmp.split()
            if len(tmp) == 2:
                entry = {} 
                entry['type'] = 'sha512' 
                entry['value'] = tmp[0] 
                result['checksum'][tmp[1]] = entry

        if (STATE_SHA512 and s.endswith('"')):
            STATE_SHA512 = False
            tmp = s.lstrip()
            tmp = tmp.strip('"')
            tmp = tmp.split()
            if len(tmp) == 2:
                entry = {} 
                entry['type'] = 'sha512' 
                entry['value'] = tmp[0] 
                result['checksum'][tmp[1]] = entry

        #
        # Security fixes
        #
        if STATE_SECFIXES:
            if re.findall(r'^#', s):
                tmp = s.replace('# ', '')
                tmp = tmp.replace('# ', '')
                if tmp != "":
                    secfixes_yaml = secfixes_yaml + tmp + "\n"

        if (s.startswith(START_SECFIXES)):
            STATE_SECFIXES = True
            secfixes_yaml = "secfixes:" + "\n"

        if (STATE_SECFIXES and not re.findall(r'^#', s)):
            STATE_SECFIXES = False
            try:
                secfixes = yaml.safe_load(secfixes_yaml)
            except BaseException:
                print(name)
                print(secfixes_yaml)
                sys.exit(1)
            else:
                secfixes_yaml = ""
                result['security'] = secfixes

    # END of parsing , pass 1 

    # https://wiki.archlinux.org/title/GNOME_package_guidelines
    #   where ${pkgver%.*} returns the major.minor package version,             \
    #   by removing the suffix of pkgver (which is the micro package version).  \
    #   E.g., if pkgver=3.28.0 then ${pkgver%.*} would return 3.28

    exp_var_map = {}
    for var in var_map:
        value = var_map[var]
        new_key = value.replace('$', "")
        if re.findall('%.*', new_key):
            new_key = new_key.replace('%.*', '')
            try:
                major_minor_maint = var_map[new_key]
            except BaseException:
                pass
            else:
                tmp = major_minor_maint.split('.')
                if len(tmp) > 2:
                    gnome_version = '.'.join(tmp[:-1])
                    exp_var_map[var] = gnome_version
                    parse_info['version'] = {}
                    parse_info['version']['src'] = major_minor_maint
                    parse_info['version']['build'] = gnome_version
        else:
            if new_key in var_map:
                exp_var_map[var] = var_map[new_key]
            else:
                exp_var_map[var] = var_map[var]

    result['var_map'] = exp_var_map

    #
    #  Find all all subpackages and expand the name
    #  $pkgname-doc -> ( replace $pkgname with name ) -> namme-doc
    #  Add two entries
    #      parent=name
    #      child=namme-doc
    #
    result['parent'] = result['pkgname']
    result['childs'] = []

    if 'subpackages' in result:
        subpackages = result['subpackages']
        for sub in subpackages:
            resolved = sub
            for key in exp_var_map:
                resolved = resolved.replace("$%s" % key, exp_var_map[key])
            result['childs'].append(resolved)

    # Dependencies 
    #  install/runtime:   depends 
    #  build: 
    #    check: checkdepends
    #    compile: makedepends
    #                 $depends_dev
    #
    tool_dep = [] 
    if 'makedepends' in result: 
      for dep in result['makedepends']: 
        if dep[0] == '$' or dep[0] == '_' : 
          key = dep[1:]
          if key in var_map and len(var_map[key]) > 0: 
            for sdep in var_map[key].split():  
              if sdep[0] == '$' or sdep[0] == '_' : 
                 skey = sdep[1:]
                 if skey in var_map and len(var_map[skey]) > 0: 
                    entry = var_map[skey] 
                 else: 
                    entry = skey
              else: 
                 entry = sdep
          else: 
            entry = key
        else: 
          entry = dep 
        tool_dep.append(entry) 
      if 'tools' not in result: 
         result['tools'] = {}
      tmp_tool_dep = {} 
      for p in tool_dep: 
        try: 
         if p in apkbuild['index'] and 'parent' in apkbuild['index'][p]: 
          tmp_tool_dep[p] = {} 
          tmp_tool_dep[p]['parent'] = apkbuild['index'][p]['parent']
        except: 
          sys.stderr.write("Problem parsing tools/makedepends\n")  
      result['tools']['makedepends'] = tmp_tool_dep
    
    check_dep = [] 

    if 'checkdepends' in result: 
      for dep in result['checkdepends']: 
        if dep[0] == '$' or dep[0] == '_' : 
          key = dep[1:]
          if key in var_map and len(var_map[key]) > 0: 
            for sdep in var_map[key].split():  
              if sdep[0] == '$' or sdep[0] == '_' : 
                 skey = sdep[1:]
                 if skey in var_map and len(var_map[skey]) > 0: 
                    entry = var_map[skey] 
                 else: 
                    entry = skey
              else: 
                 entry = sdep
          else: 
            entry = key
        else: 
          entry = dep 
        check_dep.append(entry) 
      if 'tools' not in result: 
         result['tools'] = {}
      tmp_check_dep = {} 
      for p in check_dep: 
        try: 
         if p in apkbuild['index'] and 'parent' in apkbuild['index'][p]: 
          tmp_check_dep[p] = {} 
          tmp_check_dep[p]['parent'] = apkbuild['index'][p]['parent']
        except: 
          sys.stderr.write("Problem parsing tools/checkdepends\n")  
      result['tools']['checkdepends'] = tmp_check_dep
    
    # source section consists of the following entries
    #  external code with url ://
    #  external patch with url ://
    #  local file
    #  local patch
    #  A new entry 'download' with subentries for each category
    if 'source' in result:
        prevent_duplicates = {}
        result['download'] = {}
        result['download']['external'] = {}
        result['download']['external']['patch'] = []
        result['download']['external']['code'] = []
        result['download']['internal'] = {}
        result['download']['internal']['patch'] = []
        result['download']['internal']['code'] = []
        result['download']['internal']['build'] = []
        source = result['source']
        for src in result['source']:

            # Expand vaiables

            e_path = src['remote']
            e_resolved = e_path.replace('$pkgname', result['pkgname'])
            e_resolved = e_resolved.replace('${pkgname}', result['pkgname'])
            if '_pkgname' in exp_var_map: 
               if 'pkgname_alias' not in result: 
                  result['pkgname_alias'] = exp_var_map['_pkgname']
               result['download']['internal']['build'] = []
               e_resolved = e_resolved.replace('$_pkgname', exp_var_map['_pkgname'])
            e_resolved = e_resolved.replace('${_pkgname}', result['pkgname'])
            e_resolved = e_resolved.replace('$pkgver', result['pkgver'])
            e_resolved = e_resolved.replace('${pkgver}', result['pkgver'])
            for key in exp_var_map:
                emap = "$" + key
                if e_resolved.find(emap):
                    e_resolved = e_resolved.replace(emap, exp_var_map[key])
                emap = "${" + key + "}"
                if e_resolved.find(emap):
                    e_resolved = e_resolved.replace(emap, exp_var_map[key])
                emap = "${" + key
                if e_resolved.find(emap):
                    e_resolved = e_resolved.replace(emap, exp_var_map[key])

            i_path = src['local']
            i_resolved = i_path.replace('$pkgname', result['pkgname'])
            i_resolved = i_resolved.replace('${pkgname}', result['pkgname'])
            if '_pkgname' in exp_var_map: 
               i_resolved = i_resolved.replace('$_pkgname', exp_var_map['_pkgname'])
            i_resolved = i_resolved.replace('${_pkgname}', result['pkgname'])
            i_resolved = i_resolved.replace('$pkgver', result['pkgver'])
            i_resolved = i_resolved.replace('${pkgver}', result['pkgver'])
            for key in exp_var_map:
                emap = "$" + key
                if i_resolved.find(emap):
                    i_resolved = i_resolved.replace(emap, exp_var_map[key])
                emap = "${" + key + "}"
                if i_resolved.find(emap):
                    i_resolved = i_resolved.replace(emap, exp_var_map[key])
                emap = "${" + key
                if i_resolved.find(emap):
                    i_resolved = i_resolved.replace(emap, exp_var_map[key])

            # Source that contains :// is external , download with curl ,
            # generic tyoe

            find_url = e_resolved.split('://')
            if len(find_url) == 2:
                if re.findall(r'.*[\-]*?patch$', e_resolved):
                    # External patch
                    tmp = {}
                    tmp['remote'] = {}
                    tmp['remote']['type'] = 'generic'
                    tmp['remote']['url'] = e_resolved
                    tmp['local'] = {}
                    tmp['local']['type'] = 'file'
                    tmp['local']['path'] = "%s/%s/%s" % (
                        repository, name, i_resolved)
                    if e_resolved not in prevent_duplicates:
                        result['download']['external']['patch'].append(tmp)
                        prevent_duplicates[e_resolved] = e_resolved
                else:
                    # External code
                    tmp = {}
                    tmp['remote'] = {}
                    tmp['remote']['type'] = 'generic'
                    tmp['remote']['url'] = e_resolved
                    tmp['local'] = {}
                    tmp['local']['type'] = 'file'
                    tmp['local']['path'] = "%s/%s/%s" % (
                        repository, name, i_resolved)
                    if e_resolved not in prevent_duplicates:
                        result['download']['external']['code'].append(tmp)
                        prevent_duplicates[e_resolved] = e_resolved
            else:
                if re.findall(r'.*[\-]*?patch$', e_resolved):
                    # Internal patch , remote url must be retrived with git ,
                    # url, commit and path
                    tmp = {}
                    tmp['remote'] = {}
                    tmp['remote']['type'] = 'git'
                    tmp['remote']['commit'] = repo_hash_dict[repository]
                    tmp['remote']['url'] = "git://git.alpinelinux.org/aports"
                    tmp['remote']['path'] = "%s/%s/%s" % (
                        repository, name, i_resolved)
                    tmp['local'] = {}
                    tmp['local']['type'] = 'file'
                    tmp['local']['path'] = "%s/%s/%s" % (
                        repository, name, i_resolved)
                    result['download']['internal']['patch'].append(tmp)
                else:
                    # Internal code , remote url must be retrived with git ,
                    # url, commit and path
                    tmp = {}
                    tmp['remote'] = {}
                    tmp['remote']['type'] = 'git'
                    tmp['remote']['commit'] = repo_hash_dict[repository]
                    tmp['remote']['url'] = "git://git.alpinelinux.org/aports"
                    tmp['remote']['path'] = "%s/%s/%s" % (
                        repository, name, i_resolved)
                    tmp['local'] = {}
                    tmp['local']['type'] = 'file'
                    tmp['local']['path'] = "%s/%s/%s" % (
                        repository, name, i_resolved)
                    result['download']['internal']['code'].append(tmp)

                
            tmp = {} 
            tmp['local'] = {} 
            tmp['local']['type'] = 'file'
            tmp['local']['path'] = "%s/%s/APKBUILD" % (repository, name) 
            tmp['remote'] = {}
            tmp['remote']['type'] = 'git'
            tmp['remote']['commit'] = repo_hash_dict[repository]
            tmp['remote']['url'] = "git://git.alpinelinux.org/aports"
            tmp['remote']['path'] = "%s/%s/APKBUILD" % (repository, name)

            result['download']['internal']['build'] = tmp 
    return result, parse_info

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
        {'long': '--src', 'help': 'Directory with cloned aports repository ',
         'meta': 'src', 'required': True},
        {'long': '--name', 'help': 'Name of package',
         'meta': 'name', 'required': True},
        {'long': '--output', 'help': 'outfile',
         'meta': 'output', 'required': True},
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



def main():

    # Test 
    # Build base_image so that /tmp/alpine is populated and /tmp/index.json is generated 
    # python3 apklib.py --checkout  /tmp/alpine/checkout/ --src /tmp/alpine/src/  --name  prometheus-node-exporter --apkindex /tmp/index.json  --output /tmp/a

    args = parse_cmdline()
    apkindex = import_json(args.apkindex)

    package = args.name
    if package in apkindex['index']: 
      commit_hash = apkindex['index'][package]['commit']
      repo = apkindex['index'][package]['repo']
      tmp = git_manager.checkout(commit_hash, "%s/aports" % args.src)
      dst_file = "%s/aports/%s/%s/APKBUILD" % (args.src, repo, package)
      dst_file_path = Path(dst_file)
      repos = apkindex['repos']
      repo_hash_dict = get_package_repo_from_bom(repos)
      if dst_file_path.exists():
         print("OK",commit_hash,dst_file) 
         result = {}
         result['map'], stats   = parse_apkbuild_manifest(package, repo, dst_file, repo_hash_dict, apkindex, "package")
         result['stats'] = stats
         result_json = export_json(result)
         fp = open(args.output,"w") 
         fp.write(result_json) 
         fp.close() 
         return 0
      else: 
         print("ERR",dst_file) 
         return 1 


if __name__ == '__main__':
    main()

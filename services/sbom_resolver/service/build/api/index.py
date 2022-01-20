#!/usr/bin/env python3
import os
import sys
import datetime
import argparse
import uuid
import pprint
import http
import uuid
import encodings
import codecs
import hashlib
from pathlib import Path


import connexion
from connexion import NoContent
from connexion.resolver import RestyResolver
from flask_cors import CORS
from flask import request
from flask import jsonify
from flask import Response
from flask import current_app

import jwt
import json
import traceback


import api.lib.create_apkcache as create_apkcache
import api.lib.parse_apkbuild as parse_apkbuild
import api.lib.aggregate_bom as aggregate_bom
import api.lib.git_manager as git_manager


try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

from io import BytesIO


#
# Info about exceptions in string
#
def debug_info():
    except_info = sys.exc_info()
    line = except_info[2].tb_lineno
    module = except_info[2].tb_frame.f_code.co_filename
    info = traceback.format_exception(*sys.exc_info())
    s = "\n\n--------------------------\n"
    s = "%s%s" % (
        s, "-------- TRACEBACK file: [%s] line: [%s] ------\n\n\n" % (module, line))
    for e in info:
        s = "%s%s" % (s, "    %s" % e)
        s = "%s%s" % (s, "\n\n--------------------------\n")
    return s


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
        y = {}
    return y


def post(token_info, **kwargs):

    headers = request.headers

    with current_app.app_context():
        logger = current_app.logger
        xapiid = current_app.xapiid
        title = current_app.title
        server_url = current_app.server_url
        version = current_app.version

    logger.debug("Serving POST with Connexion version: " +
                 version + " x-api-id: " + xapiid)

    APORTS_SRC = os.getenv('APORTS_SRC', '/tmp/alpine/src')
    APORTS_CHECKOUT = os.getenv('APORTS_CHECKOUT', '/tmp/alpine/checkout')
    APORTS_CACHE = os.getenv('APORTS_CACHE', '/tmp/alpine/cache')

    body = {}
    if 'body' in kwargs:
        for arg in kwargs['body'].keys():
            body[arg] = kwargs['body'][arg]

    if 'accept' in headers:
        accept = headers['accept']
    else:
        accept = "application/json"

    if 'flow-id' in headers:
        flow_id = headers['flow-id']
    else:
        flow_id = "no_flow_id_in_header"

    if 'upn' in token_info:
        upn = token_info['upn']
    else:
        upn = 'no_upn_in_token'

    images = request.files.to_dict()
    for image in images:
        logger.debug("image:%s mimetype %s\n" %
                     (image, images[image].mimetype))

    image = 'apkindex'
    metadata = {}
    TMP_FILE_NAME = "/tmp/apkindex-%s-%s.tar" % (upn, flow_id)
    if image in images:
        mtype = images[image].mimetype
        file_name = images[image].filename
        images[image].save(TMP_FILE_NAME)
        try:
            fp = open(TMP_FILE_NAME, "rb")
            buff = fp.read()
            fp.close()
        except BaseException:
            logger.debug("Problem parsing  %s\n" % debug_info())
            return connexion.problem(
                status=500, title=http.client.responses[500], detail="Unable to process APKINDEX")
        else:
            logger.debug("Parsing APKINDEX ok  \n")

        try:
            logger.debug("About to remove file %s\n" % TMP_FILE_NAME)
            os.unlink(TMP_FILE_NAME)
        except BaseException:
            logger.warning("Unable to remove temporary file %s" %
                           TMP_FILE_NAME)

    # Convert tarball with all APKINDEX.tar.gz into JSON
    apkindex = aggregate_bom.process_tarball(buff, create_commit_map=False)

    MAIN_BRANCH = os.getenv('MAIN_BRANCH', 'master')
    entry_exists, cache_index_file, aports_info = create_apkcache.create_cache(
        APORTS_SRC, MAIN_BRANCH, APORTS_CHECKOUT, APORTS_CACHE, apkindex)
    if entry_exists == True:
        tmp_json = {}
        tmp_json['info'] = "Entry exists [%s]" % cache_index_file
        return tmp_json, 200

    logger.debug("About to create %s" % cache_index_file)
    result = {}
    result['map'], stats = parse_apkbuild.scan_aports(
        APORTS_CHECKOUT, apkindex)
    result['apkindex'] = apkindex['repos']
    result['aports'] = aports_info
    result['stats'] = stats
    result_json = export_json(result)
    fp = open(cache_index_file, "w")
    fp.write(result_json)
    fp.close()
    tmp = {}
    tmp['apkindex'] = apkindex['repos']
    tmp['aports'] = aports_info
    tmp['parse'] = stats
    return tmp, 200

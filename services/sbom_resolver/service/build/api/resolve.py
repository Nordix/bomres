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
from pathlib import Path


import api.lib.resolve_bom as resolve_bom


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

    with current_app.app_context():
        logger = current_app.logger
        xapiid = current_app.xapiid
        title = current_app.title
        server_url = current_app.server_url
        version = current_app.version

    logger.debug("Serving POST " + request.path +
                 " with Connexion version: " + version + " x-api-id: " + xapiid)

    headers = request.headers

    ttl_header = 'X-Message-Ttl'
    if ttl_header in headers:
        ttl = int(headers[ttl_header])
    else:
        ttl = -1

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


    APORTS_CACHE = os.getenv('APORTS_CACHE', '/tmp/alpine/cache')


    images = request.files.to_dict()
    image = 'sbom'
    tree = {}
    TMP_FILE_NAME = "/tmp/sbom-%s-%s.json" % (upn, flow_id)
    if image in images:
        mtype = images[image].mimetype
        file_name = images[image].filename
        images[image].save(TMP_FILE_NAME)
        bom = import_json(TMP_FILE_NAME)
        try:
            os.unlink(TMP_FILE_NAME)
        except:
            error_message = "Unable to load SBOM "
            logger.debug(error_message)
            return connexion.problem(status=418, title="Inbound SBOM", detail=error_message)
        else:
            logger.debug("Loaded inbound SBOM")

        try:
            apk_hash = bom['metadata']['aggregator']['alpine']['apkindex']['hash']
        except:
            error_message = "Could not find hash for apkindex"
            logger.debug(error_message)
            return connexion.problem(status=418, title="Inbound SBOM", detail=error_message)

        cache_index_file = "%s/APKINDEX-%s.json" % (APORTS_CACHE, apk_hash)
        cache_path = Path(cache_index_file)

        if not cache_path.exists():
            logger.debug("Entry does not exists in cache ")
            tmp_json = {}
            tmp_json['info'] = "Entry does not exists [%s], please generate index " % cache_index_file
            return tmp_json, 200
        else:
            alpine_dict = import_json(cache_index_file)
            logger.debug("About to enrich bom")
            result = resolve_bom.mapper(bom, alpine_dict, False)
            logger.debug("Done")
            if ttl != -1:
                response_header = {}
                response_header[ttl_header] = str(ttl)
                logger.debug("Added response header %s %s " %
                             (ttl_header, ttl))
                return result, 200, response_header
            else:
                return result

    else:
        error_message = "Missing SBOM"
        logger.debug(error_message)
        return connexion.problem(status=418, title="Inbound SBOM", detail=error_message)

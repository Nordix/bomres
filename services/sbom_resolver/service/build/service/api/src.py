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
import bomres.lib.git_manager as git_manager


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


def search(token_info):

    with current_app.app_context():
        logger = current_app.logger
        xapiid = current_app.xapiid
        title = current_app.title
        server_url = current_app.server_url
        version = current_app.version

    logger.debug("Serving GET with Connexion version: " +
                 version + " x-api-id: " + xapiid)

    APORTS_SRC = os.getenv('APORTS_SRC', '/tmp/alpine/src')

    result = []
    try:
        fp = open("%s/uid" % APORTS_SRC, "r")
        uid = fp.read()
        fp.close()
        tmp = {}
        tmp['uuid'] = uid
        tmp['info'] = git_manager.info("%s/aports" % APORTS_SRC)
        result.append(tmp)
    except BaseException:
        logger.debug("No repo found")
        return result, 200
    else:
        return result, 200


def delete(token_info, aport_uuid):

    APORTS_SRC = os.getenv('APORTS_SRC', '/tmp/alpine/src')
    with current_app.app_context():
        logger = current_app.logger
        xapiid = current_app.xapiid
        title = current_app.title
        server_url = current_app.server_url
        version = current_app.version

    logger.debug("Serving POST with Connexion version: " +
                 version + " x-api-id: " + xapiid)

    delete = git_manager.rm(APORTS_SRC, aport_uuid)
    return delete, 200
    if delete['status'] == True:
        logger.debug(delete)
        return delete, 200
    else:
        return connexion.problem(
            status=404, title=http.client.responses[404], detail="No repo found")


def post(token_info, **kwargs):

    headers = request.headers
    with current_app.app_context():
        logger = current_app.logger
        xapiid = current_app.xapiid
        title = current_app.title
        server_url = current_app.server_url
        version = current_app.version

    APORTS_SRC = os.getenv('APORTS_SRC', '/tmp/alpine/src')

    logger.debug("Serving POST with Connexion version: " +
                 version + " x-api-id: " + xapiid)
    body = {}

    if 'body' in kwargs:
        for arg in kwargs['body'].keys():
            body[arg] = kwargs['body'][arg]

    if 'url' in body:
        logger.info("About to clone %s into %s" % (body['url'], APORTS_SRC))
        clone = git_manager.clone(APORTS_SRC, body['url'])
        logger.debug(clone)

        result = []
        if 'status' in clone and clone['status'] == True:
            tmp = {}
            tmp['uuid'] = clone['uuid']
            tmp['info'] = git_manager.info("%s/aports" % APORTS_SRC)
            result = []
            result.append(tmp)
            return result, 200
        else:
            try:
                fp = open("%s/uid" % APORTS_SRC, "r")
                uid = fp.read()
                fp.close()
                tmp = {}
                tmp['uuid'] = uid
                tmp['info'] = git_manager.info("%s/aports" % APORTS_SRC)
                tmp['detail'] = 'Repository exists'
                result.append(tmp)
            except BaseException:
                logger.debug("No repo found")
                return connexion.problem(
                    status=201, title=http.client.responses[201], detail="Unable to clone repo")
            else:
                return result, 200

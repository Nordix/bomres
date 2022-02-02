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


def post(token_info, **kwargs):

    with current_app.app_context():
        logger = current_app.logger
        xapiid = current_app.xapiid
        title = current_app.title
        server_url = current_app.server_url
        version = current_app.version

    logger.debug("Serving POST " + request.path +
                 " with Connexion version: " + version + " x-api-id: " + xapiid)

    if 'body' in kwargs and 'path' in kwargs['body'] and 'commit' in kwargs['body']:
        body = kwargs['body']
        logger.debug(body)
    else:
        message = "Bad indata"
        logger.warning(message)
        return connexion.problem(status=400, title='Parsing', detail=message)

    APORTS_SRC = os.getenv('APORTS_SRC', '/tmp/alpine/src')
    path = "%s/aports/%s" % (APORTS_SRC, body['path'])

    # Assume that the repo is in the correct state
    try:
        fp = open(path, "r")
        buffer = fp.read()
        fp.close()
    except BaseException:
        # If not found , checkout the requested commit state
        git_manager.checkout(body['commit'], "%s/aports" % APORTS_SRC)
        try:
            fp = open(path, "r")
            buffer = fp.read()
            fp.close()
        except BaseException:
            message = "Cannot find %s at commit state %s in repo %s" % (
                body['path'], body['commit'], body['repository_id'])
            logger.warning(message)
            return connexion.problem(
                status=404, title='Not found', detail=message)
    else:
        logger.debug("Found file, about to reply")
        return Response(buffer, status=200, mimetype='text/plain')

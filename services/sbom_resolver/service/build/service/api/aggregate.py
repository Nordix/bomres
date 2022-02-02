#!/usr/bin/env python3
import os
import sys
import datetime
import argparse
import uuid
import pprint
import http
import traceback
from inspect import getframeinfo, stack
import time
import tempfile


import connexion
from connexion import NoContent
from connexion.resolver import RestyResolver

from flask import request
from flask import jsonify
from flask import Response
from flask import current_app

import jwt
import json

import bomres.lib.aggregate_bom as aggregate_bom


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


def debuginfo(comment):
    caller = getframeinfo(stack()[1][0])
    tmp = {}
    tmp['application'] = {}
    tmp['application']['file'] = os.path.basename(caller.filename)
    tmp['application']['lineno'] = caller.lineno
    tmp['application']['comment'] = comment
    tmp['middleware'] = {}
    tmp['middleware']['connexion'] = connexion.__version__
    try:
        fp = open("/proc/version", "r")
        version = fp.read().replace('\n', '')
        fp.close()
    except BaseException:
        pass
    else:
        tmp['base'] = {}
        tmp['base']['kernel'] = version
    return tmp


def post(token_info, **kwargs):

    with current_app.app_context():
        logger = current_app.logger
        xapiid = current_app.xapiid
        title = current_app.title
        server_url = current_app.server_url
        version = current_app.version

    logger.debug("Serving POST with Connexion version: " +
                 version + " x-api-id: " + xapiid)

    headers = request.headers

    for head in headers:
        if 'Authorization' in head[0]:
            token = headers['Authorization']

    if 'accept' in headers:
        accept = headers['accept']
    else:
        accept = "application/json"
    logger.debug("Accept mime type  %s\n" % accept)

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

    image = 'config'
    settings = ""
    TMP_FILE_NAME = "/tmp/config-%s-%s.bom" % (upn, flow_id)
    os_path = TMP_FILE_NAME
    if image in images:
        os_file = True
        file_name = images[image].filename
        images[image].save(TMP_FILE_NAME)
        mtype = images[image].mimetype
        fp = open(TMP_FILE_NAME)
        settings = fp.read()
        fp.close()
    else:
        try:
            os.unlink(TMP_FILE_NAME)
        except BaseException:
            pass

    image = 'desired'
    desired = ""
    TMP_FILE_NAME = "/tmp/desired-%s-%s.bom" % (upn, flow_id)
    os_path = TMP_FILE_NAME
    if image in images:
        os_file = True
        file_name = images[image].filename
        images[image].save(TMP_FILE_NAME)
        mtype = images[image].mimetype
        fp = open(TMP_FILE_NAME)
        desired = fp.read()
        fp.close()
    else:
        try:
            os.unlink(TMP_FILE_NAME)
        except BaseException:
            pass
    image = 'resolved'
    TMP_FILE_NAME = "/tmp/os-%s-%s.bom" % (upn, flow_id)
    resolved_bom = ""
    if image in images:
        os_file = True
        file_name = images[image].filename
        images[image].save(TMP_FILE_NAME)
        fp = open(TMP_FILE_NAME)
        resolved_bom = fp.read()
        fp.close()
        try:
            os.unlink(os_path)
        except BaseException:
            pass

    image = 'pkgindex'
    pkgindex = ""
    TMP_FILE_NAME = "/tmp/metadata-%s-%s.tar" % (upn, flow_id)
    if image in images:
        mtype = images[image].mimetype
        file_name = images[image].filename
        images[image].save(TMP_FILE_NAME)
        try:
            fp = open(TMP_FILE_NAME, "rb")
            pkgindex = fp.read()
            fp.close()
        except BaseException:
            logger.debug("Problem parsing  %s\n" % TMP_FILE_NAME)
            logger.debug("Problem parsing  %s\n" % debug_info())
            return connexion.problem(
                status=500, title=http.client.responses[500], detail=debug_info())
        else:
            logger.debug("Parsing APKINDEX ok  \n")

        try:
            logger.debug("About to remove file %s\n" % TMP_FILE_NAME)
            os.unlink(TMP_FILE_NAME)
        except BaseException:
            logger.warning("Unable to remove temporary file %s" %
                           TMP_FILE_NAME)

    if accept == "application/json":
        resolved, stats = aggregate_bom.process_resolved_bom(resolved_bom)
        desired_list = aggregate_bom.process_desired_bom(desired)
        settings_dict = aggregate_bom.process_config(settings)
        alpine_apk_index = aggregate_bom.process_tarball(pkgindex)
        mdata = aggregate_bom.format_dep(
            resolved, alpine_apk_index, desired_list, settings_dict)
        return mdata, 200

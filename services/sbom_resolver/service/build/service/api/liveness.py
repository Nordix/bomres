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



def search():

    with current_app.app_context():
        logger = current_app.logger
        xapiid = current_app.xapiid
        title = current_app.title
        server_url = current_app.server_url
        version = current_app.version

    logger.debug("Serving GET with Connexion version: " +
                 version + " x-api-id: " + xapiid)


    tmp = {} 
    tmp['statusCode'] = '200' 
    tmp['additionalInformation'] = 'Ok' 

    return tmp , 200


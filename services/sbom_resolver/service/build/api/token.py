#!/usr/bin/env python3
#
# https://opensource.zalando.com/restful-api-guidelines/#http-status-codes-and-errors
# https://github.com/zalando/connexion/issues/357
#
import os
import sys
import datetime
import argparse
import uuid
import pprint
import subprocess


import logging
from logging.config import dictConfig

import http
import connexion
from connexion import NoContent
from flask_cors import CORS
from flask import current_app
from flask import request
from flask import jsonify
from flask import Response

import jwt
import json
import base64
from basicauth import decode


from jwcrypto import jwk, jwe, jwt
from jwcrypto.common import json_encode, json_decode

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO
import traceback
import shutil


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
# JSON import
#
def import_json(input_file):
    try:
        fp = open(input_file, "r")
        data = fp.read()
        fp.close()
        y = json.loads(data)
    except BaseException:
        log = debug_info()
        y = {}
        y['error'] = log

    return y


def issue_token(priv, duration, claims):

    priv = priv.encode('ascii')

    signer = jwk.JWK()
    signer.import_from_pem(priv, password=None)

    now_epoch = datetime.datetime.utcnow().strftime('%s')
    now = datetime.datetime.utcnow()
    exp_epoch = (now + datetime.timedelta(seconds=duration)).strftime('%s')
    claims['iat'] = now_epoch
    claims['exp'] = exp_epoch

    # sign the JWT
    # specify algorithm needed for JWS
    header = {
        u'alg': 'RS256',
        'customSigHeader': 'customHeaderContent'
    }
    # generate JWT
    T = jwt.JWT(header, claims)

    T.make_signed_token(signer)
    signed_token = T.serialize(compact=True)
    return signed_token


def post(**kwargs):

    with current_app.app_context():
        logger = current_app.logger
        xapiid = current_app.xapiid
        version = current_app.version

    logger.debug("Serving POST with Connexion version: " +
                 version + " x-api-id: " + xapiid)

    #
    # How long the the access token is valid, defined by environment variable
    #
    expires_in = int(os.getenv('TOKEN_EXPIRE', '3600'))
    logger.debug("Minted access about to expire in  %d seconds " % expires_in)

    #
    # This mimic the static claim mapper in Keycloak
    #
    claims = {}
    claims['resolvers'] = {}
    claims['resolvers']['base_os'] = 'alpine'

    #
    # Issuer of access token retrived from environment
    #
    issuer = os.getenv('ISSUER', 'bomresolver')
    claims['iss'] = issuer
    logger.debug("Issuer %s" % issuer)

    #
    # All posted data about to be stored in comp dictionary
    #
    comp = {}
    if 'body' in kwargs:
        for arg in kwargs['body'].keys():
            comp[arg] = kwargs['body'][arg]

    #
    # Some parameter may be posted in the header, which have security implications
    #
    headers = connexion.request.headers
    if 'Authorization' in headers:
        # Enforce use of client credentials in request body for password grant
        if 'grant_type' in comp and comp['grant_type'] == 'password':
            error_message = "Passing client_id and client_secret in header is not secure"
            logger.error(error_message)
            return connexion.problem(
                status=400, title="Weak Security", detail=error_message)

        # Extract client credentials from header and append to body
        try:
            temp = headers['Authorization'].split()[1]
            client_id, client_secret = decode(temp)
        except BaseException:
            error_message = "Unable to decode credentials passed in header "
            logger.error(error_message)
            return connexion.problem(
                status=400, title="Security", detail=error_message)

        logger.debug("client_id and client_secret passed in header")
        comp['client_id'] = client_id
        comp['client_secret'] = client_secret

    if 'client_secret' in comp and len(comp['client_secret']) > 0:
        logger.debug("Confidential client with client_secret ")
    else:
        logger.warning("Potentially weak security: Public client")

    #
    # Each minted token should have unique identifier
    #
    jti = str(uuid.uuid4())
    claims['jti'] = jti
    logger.debug("jti: %s", jti)

    #
    # All selected scopes show up as group claims , very simple authorization
    #
    if 'scope' in comp:
        logger.debug("scope: %s" % comp['scope'])
        claims['scope'] = comp['scope']
        claims["groups"] = []
        for scope in comp['scope'].split():
            claims["groups"].append(scope)

    #
    # Reserve entry in PLM , add as claim in token
    #

    claims["upn"] = comp['client_id']

    #
    # Create signed access token
    #
    TOKEN_SIGN_KEY = os.getenv('TOKEN_SIGN_KEY', 'priv.pem')
    logger.debug("Retrieved TOKEN_SIGN_KEY  [%s]" % TOKEN_SIGN_KEY)
    try:
        fp = open(TOKEN_SIGN_KEY, "r")
        signer_key = fp.read()
        fp.close()
    except BaseException:
        error_message = "Failed to retrieve TOKEN_SIGN_KEY  [%s]" % TOKEN_SIGN_KEY
        logger.error(error_message)
        return connexion.problem(
            status=500, title="Incomplete configuration", detail=error_message)
    logger.debug("About to Sign access token")
    access_token = issue_token(signer_key, expires_in, claims)
    logger.debug("Signed ...")

    #
    # Put access token in a bearer token
    #
    logger.debug("About to created bearer token")
    bearer = {}
    bearer['access_token'] = access_token
    bearer['expires_in'] = expires_in
    bearer['token_type'] = "bearer"

    # CORS Related headers, added by analyzing keycloak
    response_header = {}
    response_header['Access-Control-Allow-Credentials'] = 'true'
    response_header['Access-Control-Allow-Origin'] = '*'
    response_header['Access-Control-Expose-Header'] = 'Access-Control-Allow-Methods'
    response_header['server'] = 'IAFW 1.0.0'

    return bearer, 200, response_header

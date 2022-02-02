#!/usr/bin/env python3

import os
import sys
import yaml


import connexion
from connexion.resolver import RestyResolver
from flask import current_app
from flask_cors import CORS
import jwt
import logging
import logging.config
import pkg_resources


from yaml import Loader, Dumper


def load_yaml(yaml_file_path):
    if os.path.exists(yaml_file_path):
        with open(os.path.realpath(yaml_file_path), 'r') as stream:
            return yaml.load(stream, Loader=Loader)


def verifyToken(token):
    try:
        tkn = jwt.decode(token, options={"verify_signature": False})
    except jwt.ExpiredSignature:
        tkn = {'error': 'Expired token'}
    return tkn


logging_config = dict(
    version=1,
    formatters={
        'f': {'format':
              '%(asctime)s %(name)-12s %(levelname)-8s %(message)s'}
    },
    handlers={
        'h': {'class': 'logging.StreamHandler',
              'formatter': 'f',
              'level': logging.DEBUG}
    },
    root={
        'handlers': ['h'],
        'level': logging.DEBUG,
    },
)


def load_openapi(path):

    try:
        open_api = load_yaml(path)
    except BaseException:
        return None

    try:
        xapi_id = open_api['info']['x-api-id']
    except BaseException:
        xapi_id = None
    try:
        title = open_api['info']['title']
    except BaseException:
        title = None

    try:
        server_url = open_api['servers'][0]['url']
    except BaseException:
        server_url = "-"

    return xapi_id, title, server_url


def main():

    os.environ["TOKENINFO_FUNC"] = "app.verifyToken"

    logging.config.dictConfig(logging_config)
    logger = logging.getLogger()

    openapi_spec = 'openapi.yaml'
    xapi_id, title, server_url = load_openapi(openapi_spec)
    if xapi_id is None:
        sys.stderr.write("Could not extract x-api-id from %s\n" % openapi_spec)
        sys.exit(1)

    app = connexion.FlaskApp(__name__)

    with app.app.app_context():
        current_app.logger = logger
        current_app.xapiid = xapi_id
        current_app.title = title
        current_app.server_url = server_url
        current_app.version = connexion.__version__

    app.add_api(openapi_spec, resolver=RestyResolver('api'))

    CORS(app.app)

    logger.debug("Start version of connexion: " + connexion.__version__)

    app.run(
        port=int(os.getenv('TARGETPORT', '8080')),
        use_reloader=False,
        threaded=False,
        debug=True
    )


if __name__ == '__main__':
    main()

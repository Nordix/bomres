import sys
import pprint
import argparse
import re
import pycurl


import pycurl_requests as requests
from requests_toolbelt.multipart.encoder import MultipartEncoder


def get(url, headers, sucess_codes, connection_timeout=5, session_timeout=60, secure=False): 


    with requests.Session() as session:

      # No root CA in place, disable control
      if secure == False: 
        session.curl.setopt(pycurl.SSL_VERIFYPEER, False)
        session.curl.setopt(pycurl.SSL_VERIFYHOST, False)
        session.curl.setopt(pycurl.CAPATH, None)

      #session.curl.setopt(pycurl.VERBOSE, True)

      # Timeout for connect and duration
      session.curl.setopt(pycurl.CONNECTTIMEOUT, connection_timeout)
      session.curl.setopt(pycurl.TIMEOUT, session_timeout)

      # Use HTTP protocol 1.1
      session.curl.setopt(pycurl.HTTP_VERSION, pycurl.CURL_HTTP_VERSION_1_1)

      r = session.get(url, headers=headers)
      result = {}
      if r.status_code in sucess_codes:
       result['data'] = r.text
       result['headers'] = r.headers
       result['status'] = 'ok'
       result['code'] = r.status_code
      else:
       result['error'] = 'Unable to contact %s' % url
       result['code'] = r.status_code
       result['status'] = 'error'
       result['debug'] = r.text
      return result
      


if __name__ == '__main__':

    # --base aggregate/alpine --path resolve --method post 

    import argparse
    args_options = {'opt': [{'long': '--debug',
                         'help': 'Debug mode'},
                        ],
                'opt_w_arg': [{'long': '--url',
                               'help': 'Specify url',
                               'meta': 'url',
                               'required': True},
                              {'long': '--method',
                               'help': 'Method ( POST,GET, PATCH etc )',
                               'meta': 'method',
                               'required': True},
                              {'long': '--token',
                               'help': 'path to token',
                               'meta': 'token',
                               'required': False}
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


    args = parse_cmdline() 


    if args.method == "get" : 
       headers={} 
       sucess_codes = [200]
       get(args.url, headers, sucess_codes, connection_timeout=5, session_timeout=60, secure=False)
       sys.exit(0) 

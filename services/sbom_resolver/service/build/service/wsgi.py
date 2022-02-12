# The link below may be useful to complete the task 
# https://www.digitalocean.com/community/tutorials/how-to-set-up-uwsgi-and-nginx-to-serve-python-apps-on-ubuntu-14-04
# https://uwsgi-docs.readthedocs.io/en/latest/WSGIquickstart.html
# https://github.com/spec-first/connexion/issues/981

#
def application(env, start_response):
    start_response('200 OK', [('Content-Type','text/html')])
    return [b"uwsgi and python, integration with connexion remains "]





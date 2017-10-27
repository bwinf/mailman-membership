#!/usr/bin/env python3

from wsgiref.simple_server import make_server
import mailman_membershipmanager

httpd = make_server('0.0.0.0', 8080, mailman_membershipmanager.app)

# httpd.handle_request() # single request
httpd.serve_forever() # many requests

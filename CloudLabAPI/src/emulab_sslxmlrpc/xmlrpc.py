#! /usr/bin/env python
#
# Copyright (c) 2004-2021 University of Utah and the Flux Group.
# 
# {{{EMULAB-LICENSE
# 
# This file is part of the Emulab network testbed software.
# 
# This file is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at
# your option) any later version.
# 
# This file is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public
# License for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with this file.  If not, see <http://www.gnu.org/licenses/>.
# 
# }}}
# 

from __future__ import print_function
import sys
import os
import pwd
import errno
import ssl
import socket
import re
import string

try:
    import xmlrpclib
except:
    import xmlrpc.client as xmlrpclib
    pass

#
# The package version number, the server wants to see this.
#
PACKAGE_VERSION = 0.1

# Default server
XMLRPC_SERVER   = "boss.emulab.net"
XMLRPC_PORT     = 3069
SERVER_PATH     = "/usr/testbed"

#
# See https://gitlab.flux.utah.edu/emulab/emulab-devel/-/blob/master/clientside/xmlrpc/emulabclient.py.in
#
RESPONSE_SUCCESS        = 0
RESPONSE_BADARGS        = 1
RESPONSE_ERROR          = 2
RESPONSE_FORBIDDEN      = 3
RESPONSE_BADVERSION     = 4
RESPONSE_SERVERERROR    = 5
RESPONSE_TOOBIG         = 6
RESPONSE_REFUSED        = 7  # Emulab is down, try again later.
RESPONSE_TIMEDOUT       = 8
RESPONSE_SEARCHFAILED   = 12
RESPONSE_ALREADYEXISTS  = 17

class EmulabResponse:
    def __init__(self, code, value=0, output=""):
        self.code     = code            # A RESPONSE code
        self.value    = value           # A return value; any valid XML type.
        self.output   = re.sub(         # Pithy output to print
            r'[^' + re.escape(string.printable) + ']', "", output)
        
        return
    def __str__(self):
        return f'{self.code} {self.value} {self.output}'
    pass

class EmulabXMLRPC:
    def __init__(self, args):
        self.debug      = args.get("debug", False)
        self.impotent   = args.get("impotent", False)
        self.verify     = args.get("verify", False)
        self.server     = XMLRPC_SERVER
        self.port       = XMLRPC_PORT
        self.path       = args.get("path", SERVER_PATH)
        self.login_id   = os.getenv("USER")
        self.cacert     = None

        if "server" in args:
            self.server = args["server"]
            pass
        if "port" in args:
            self.port = args["port"]
            pass
        if "login_id" in args:
            self.login_id = args["login_id"]
            pass
        if "ca_certificate" in args:
            self.cacert = args["ca_certificate"]
            pass

        #
        # If no certificate provided, look for the it in the users .ssl
        # directory.
        #
        if not "certificate" in args:
            try:
                pw = pwd.getpwuid(os.getuid())
                pass
            except KeyError:
                raise Exception("error: unknown user id %d" % os.getuid())

            self.certificate = os.path.join(pw.pw_dir, ".ssl", "emulab.pem")
        else:
            self.certificate = args["certificate"]
            pass

        if not os.access(self.certificate, os.R_OK):
            raise Exception("error: certificate cannot be read: %s\n" %
                             self.certificate)
        
        #
        # Verification is optional, check certificate.
        #
        if self.verify:
            if self.cacert == None:
                raise Exception("error: Must provide CA certificate\n")
            
            if not os.access(self.cacert, os.R_OK):
                raise Exception("error: CA certificate cannot be read: %s\n" %
                                self.cacert)
            pass

        URI = "https://" + self.server + ":" + str(self.port) + self.path
        ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        try:
            ctx.set_ciphers("DEFAULT:@SECLEVEL=0")
        except:
            pass
        ctx.load_cert_chain(self.certificate)
        
        if not self.verify:
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
        else:
            ctx.load_verify_locations(cafile=self.cacert)
            ctx.verify_mode = ssl.CERT_REQUIRED
            pass
    
        # Get a handle on the server,
        self.server = xmlrpclib.ServerProxy(URI, context=ctx,
                                            verbose=self.debug)
        return;
    
    def do_method(self, module, method, params):
        if self.debug:
            print(module + " " + method + " " + str(params))
            pass
        if self.impotent:
            return 0;


        # Get a pointer to the function we want to invoke.
        meth      = getattr(self.server, module + "." + method)
        meth_args = [ PACKAGE_VERSION, params ]

        #
        # Make the call. 
        #
        try:
            response = meth(*meth_args)
            pass
        except socket.error as e:
            rval = -1;
            if e.args[0] == errno.ECONNREFUSED:
                rval = RESPONSE_NETWORK_ERROR
                pass
            return (rval, None)
        except Exception as e:
            return (-1, None)

        #
        # Parse the Response, which is a dictionary. See EmulabResponse above
        # which mirrors emulabclient.py.
        #
        response = EmulabResponse(response["code"],
                                  response["value"], response["output"])

        rval = response.code
        
        #
        # If the code indicates failure, look for a "value". Use that as the
        # return value instead of the code. 
        # 
        if rval != RESPONSE_SUCCESS:
            if response.value:
                rval = response.value
                pass
            pass
        return (rval, response)

    pass



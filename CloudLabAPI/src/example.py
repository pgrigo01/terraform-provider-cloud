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

#
# Simple demonstration to get the status of an experiment using the library.
#

from __future__ import print_function
import sys
import pwd
import getopt
import os
import json
import emulab_sslxmlrpc
import emulab_sslxmlrpc.client
import emulab_sslxmlrpc.client.api as api
import emulab_sslxmlrpc.xmlrpc as xmlrpc

#
# Print the usage statement to stdout.
#
def usage():
    print("Usage: example.py [xmlrpc options] pid,name")
    wrapperoptions();

def wrapperoptions():
    print("")
    print("Wrapper Options:")
    print("    --help      Display this help message")
    print("    --server    Set the server hostname")
    print("    --port      Set the server port")
    print("    --login     Set the login id")
    print("    --cert      Specify the path to your testbed SSL certificate")
    print("    --cacert    The path to the CA certificate to use for server verification")
    print("    --verify    Enable SSL verification; defaults to disabled")
    print("    --debug     Turn on semi-useful debugging")
    return

def main():
    config = {
        "debug"    : 0,
        "impotent" : 0,
        "verify"   : 0,
    }
    
    try:
        # Parse the options,
        opts, req_args = getopt.getopt(sys.argv[1:], "",
                                       ["help", "server=", "port=",
                                        "login=", "cert=", "impotent",
                                        "debug", "cacert=", "verify"])

        for opt, val in opts:
            if opt in ("-h", "--help"):
                usage()
                sys.exit()
                pass
            elif opt == "--server":
                config["server"] = val
                pass
            elif opt == "--port":
                config["port"] = int(val)
                pass
            elif opt == "--login":
                config["login_id"] = val
                pass
            elif opt == "--cert":
                config["certificate"] = val
                pass
            elif opt == "--cacert":
                config["ca_certificate"] = val
                pass
            elif opt == "--verify":
                config["verify"] = True
                pass
            elif opt == "--debug":
                config["debug"] = 1
                pass
            elif opt == "--impotent":
                config["impotent"] = 1
                pass
            pass
        pass
    except getopt.error as e:
        print(e.args[0])
        usage()
        sys.exit(2)
        pass

    if len(req_args) != 1:
        usage()
        sys.exit(-1);
        pass

    params = {
        "experiment" : req_args[0],
        "asjson"     : True,
    }
    try:
        rpc = xmlrpc.EmulabXMLRPC(config)
        pass
    except Exception as e:
        print(e.args[0])
        sys.exit(1)
        pass
    
    (exitval,response) = api.experimentStatus(rpc, params).apply();
    if exitval:
        print(response.value)
        sys.exit(exitval)
        pass

    # Convert json string. 
    status = json.loads(response.value);
    print(status)
    pass

main()

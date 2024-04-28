#! /usr/bin/env python
#
# Copyright (c) 2004-2022 University of Utah and the Flux Group.
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
# Wrapper to convert select commands into XMLRPC calls to boss. The point
# is to provide a script interface that is backwards compatable with the
# pre-rpc API, but not have to maintain that interface beyond this simple
# conversion.
#
from __future__ import print_function
import errno
import sys
import pwd
import getopt
import os
import traceback
import emulab_sslxmlrpc
import emulab_sslxmlrpc.client
import emulab_sslxmlrpc.client.api as api
import emulab_sslxmlrpc.xmlrpc as xmlrpc

#
# Print the usage statement to stdout.
#
def usage():
    print("Usage: wrapper [wrapper options] command [command args and opts]")
    print("")
    print("Commands:")
    for key, val in api.Handlers.items():
        print(("    %-12s: %s." % (key, val["help"])))
        pass
    print("(Specify the --help option to specific commands for more help)")
    wrapperoptions();
    print
    print("Example:")
    print("  "
           + "script_wrapper"
           + " --server=boss.emulab.net experimentStatus testbed,one-node")

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
    
    #
    # Process program arguments. There are two ways we could be invoked.
    # 1) as the wrapper, with the first required argument the name of the script.
    # 2) as the script, with the name of the script in argv[0].
    # ie:
    # 1) wrapper --server=boss.emulab.net node_admin -n pcXXX
    # 2) node_admin --server=boss.emulab.net -n pcXXX
    #
    # So, just split argv into the first part (all -- args) and everything
    # after that which is passed to the handler for additional getopt parsing.
    #
    wrapper_argv = [];
    wrapper_opts = [ "help", "server=", "port=", "login=", "cert=",
                     "impotent", "debug", "cacert=", "verify" ]

    for arg in sys.argv[1:]:
        if arg.startswith("--") and arg[2:arg.find("=")+1] in wrapper_opts:
            wrapper_argv.append(arg);
            pass
        else:
            break
        pass

    try:
        # Parse the options,
        opts, req_args =  getopt.getopt(wrapper_argv[0:], "", wrapper_opts)
        # ... act on them appropriately, and
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

    #
    # Okay, determine if argv[0] is the name of the handler, or if this was
    # invoked generically (next token after wrapper args is the name of the
    # handler).
    #
    handler      = None;
    command_argv = None;

    if os.path.basename(sys.argv[0]) in api.Handlers:
        handler      = os.path.basename(sys.argv[0])
        command_argv = sys.argv[len(wrapper_argv) + 1:];
        pass
    elif (len(wrapper_argv) == len(sys.argv) - 1):
        # No command token was given.
        usage();
        sys.exit(-2);
        pass
    else:
        token = sys.argv[len(wrapper_argv) + 1];

        if token not in api.Handlers:
            print("Unknown script command, ", token)
            usage();
            sys.exit(-1);
            pass

        handler      = token
        command_argv = sys.argv[len(wrapper_argv) + 2:]
        pass

    try:
        rpc = xmlrpc.EmulabXMLRPC(config)
        pass
    except Exception as e:
        traceback.print_exc()
        sys.exit(1)
        pass
    
    instance = api.Handlers[handler]["class"](rpc)
    if instance.parseArgs(command_argv):
        wrapperoptions();
        sys.exit(1)
        pass
    (exitval,response)  = instance.apply()    

    try:
        if len(response.output):
            pass
    except AttributeError as err:
        sys.exit(1)
        pass
    
    sys.exit(exitval);
    pass

def startExperiment():
    main()
    pass

def modifyExperiment():
    main()
    pass

def terminateExperiment():
    main()
    pass

def experimentStatus():
    main()
    pass

def extendExperiment():
    main()
    pass

def experimentManifests():
    main()
    pass

def experimentReboot():
    main()
    pass

def connectExperiment():
    main()
    pass

def disconnectExperiment():
    main()
    pass

if __name__ == "__main__":
    main()

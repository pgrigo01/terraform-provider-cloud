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
# A more complex example demonstrating an experiment workflow that starts
# an experiment, waits for the execute service to run, and terminates the
# experiment. 
#

from __future__ import print_function
import sys
import pwd
import getopt
import os
import time
import json
import emulab_sslxmlrpc
import emulab_sslxmlrpc.client
import emulab_sslxmlrpc.client.api as api
import emulab_sslxmlrpc.xmlrpc as xmlrpc

#
# 
#
def usage():
    print("Usage: workflow.py [xmlrpc options] profile project name")
    print("where:")
    print("profile     - UUID or pid,name of an existing profile")
    print("project     - Name of a project you are a member of")
    print("name        - Pithy name for your new experiment")
    wrapperoptions();

def wrapperoptions():
    print("")
    print("xmlrpc Options:")
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

    if len(req_args) != 3:
        usage()
        sys.exit(-1);
        pass

    try:
        rpc = xmlrpc.EmulabXMLRPC(config)
        pass
    except Exception as e:
        print(e.args[0])
        sys.exit(1)
        pass

    #
    # Start the experiment.
    #
    startexp = 1
    if startexp:
        print("Trying to start your experiment")
        params = {
            "profile" : req_args[0],
            "proj"    : req_args[1],
            "name"    : req_args[2]
        }
        (exitval,response) = api.startExperiment(rpc, params).apply();
        if exitval:
            print(response.output)
            sys.exit(exitval);
            pass
        print("Experiment is starting up, checking status periodically")
        pass

    #
    # Now wait for the experiment to finishing setting up, run the install
    # script, and report status. Or a fatal error along the way.
    #
    params = {
        "experiment" : req_args[1] + "," +  req_args[2],
        "asjson"     : True
    }
    while True:
        time.sleep(15)
        
        (exitval,response) = api.experimentStatus(rpc, params).apply();

        if exitval:
            code = response.value
            
	    if (code == api.GENIRESPONSE_REFUSED or
                code == api.GENIRESPONSE_NETWORK_ERROR):
                print("Server is offline, waiting for a bit")
		continue
            elif code == api.GENIRESPONSE_BUSY:
		print("Experiment is busy, waiting for a bit")
                continue
            elif code == api.GENIRESPONSE_SEARCHFAILED:
		print("Experiment is gone")
		sys.exit(code)
                pass
	    else:
		# Everything else is bad news. A positive error code
		# typically means we could not get to the cluster. But
		# the experiment it marked for cancel, and eventually
		# it is going to happen.
		print(response.output)
                sys.exit(code)
                pass
            pass

        status = json.loads(response.value)
        #print(status)

        #
        # Waiting to go ready or failed.
        #
        if status["status"] == "failed":
            print("Experiment failed to instantiate")
            break

        #
        # Once we hit ready, waiting for the execute service to exit.
        #
        if status["status"] == "ready":
            #
            # If there is no execute service, then no point in waiting
            #
            if not "execute_status" in status:
                print("No execute service to wait for!")
                break

            total    = status["execute_status"]["total"]
            finished = status["execute_status"]["finished"]

            if total == finished:
                print("Execute services have finished")
                break
            else:
                print("Still waiting for execute service to finish")
                continue
            pass

        print("Still waiting for experiment to go ready")
        pass
    #
    # Terminate the experiment. 
    #
    print("Terminating experiment")
    (exitval,response) = api.terminateExperiment(rpc, params).apply();
    if exitval:
        print(response.output)
        sys.exit(exitval);
        pass
    print("Experiment is terminating")
    sys.exit(0)
    pass

main()

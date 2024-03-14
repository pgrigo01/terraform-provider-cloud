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
from __future__ import print_function
import getopt
import xmlrpc as sslxmlrpc
import json



#
# start a portal experiment
#
class startExperiment:
    def __init__(self, xmlrpc, params=None):
        self.xmlrpc = xmlrpc
        self.params = params
        pass

    def parseArgs(self, argv):
        self.params = {}

        try:
            opts, req_args = getopt.getopt(
                argv,
                "a:p:Ps",
                [
                    "help",
                    "name=",
                    "duration=",
                    "project=",
                    "site=",
                    "start=",
                    "bindings=",
                    "sshpubkey=",
                    "stop=",
                    "paramset=",
                    "refspec=",
                ],
            )
            pass
        except getopt.error as e:
            print(e.args[0])
            self.usage()
            return -1

        for opt, val in opts:
            if opt in ("-h", "--help"):
                self.usage()
                return 1
            elif opt == "-a":
                self.params["aggregate"] = val
                pass
            elif opt == "-P":
                self.params["nopending"] = 1
                pass
            elif opt == "-s":
                self.params["noemail"] = 1
                pass
            elif opt == "--name":
                self.params["name"] = val
                pass
            elif opt == "--duration":
                self.params["duration"] = val
                pass
            elif opt in ("-p", "--project"):
                self.params["proj"] = val
                pass
            elif opt == "--start":
                self.params["start"] = val
                pass
            elif opt == "--stop":
                self.params["stop"] = val
                pass
            elif opt == "--paramset":
                self.params["paramset"] = val
                pass
            elif opt == "--bindings":
                self.params["bindings"] = val
                pass
            elif opt == "--refspec":
                self.params["refspec"] = val
                pass
            elif opt == "--site":
                self.params["site"] = val
                pass
            elif opt == "--sshpubkey":
                params["sshpubkey"] = val
                pass
            pass

        # Do this after so --help is seen.
        if len(req_args) != 1:
            self.usage()
            return -1

        self.params["profile"] = req_args[0]
        return 0

    def apply(self):
        if self.params == None:
            raise Exception("No arguments provided")

        rval, response = self.xmlrpc.do_method("portal", "startExperiment", self.params)
        return (rval, response)

    def usage(self):
        print("Usage: startExperiment <options> ", end=" ")
        print("[--site 'site:1=aggregate ...'] <profile>")
        print("where:")
        print(" -w           - Wait mode (wait for experiment to start)")
        print(" -a urn       - Override default aggregate URN")
        print(" --project    - pid[,gid]: project[,group] for new experiment")
        print(" --name       - Optional pithy name for experiment")
        print(" --duration   - Number of hours for initial expiration")
        print(" --start      - Schedule experiment to start at (unix) time")
        print(" --stop       - Schedule experiment to stop at (unix) time")
        print(" --paramset   - uid,name of a parameter set to apply")
        print(" --bindings   - json string of bindings to apply to parameters")
        print(" --refspec    - refspec[:hash] of a repo based profile to use")
        print(" --site       - Bind sites used in the profile")
        print("profile       - Either UUID or pid,name")
        return

    pass


#
# modify a portal experiment
#
class modifyExperiment:
    def __init__(self, xmlrpc, params=None):
        self.xmlrpc = xmlrpc
        self.params = params
        pass

    def parseArgs(self, argv):
        self.params = {}

        try:
            opts, req_args = getopt.getopt(
                argv, "a:P", ["help", "experiment=", "bindings="]
            )
            pass
        except getopt.error as e:
            print(e.args[0])
            self.usage()
            return -1

        for opt, val in opts:
            if opt in ("-h", "--help"):
                self.usage()
                return 1
            elif opt == "-a":
                self.params["aggregate"] = val
                pass
            elif opt == "-P":
                self.params["nopending"] = 1
                pass
            elif opt == "--bindings":
                self.params["bindings"] = val
                pass
                pass
            pass

        # Do this after so --help is seen.
        if len(req_args) != 1:
            self.usage()
            return -1

        self.params["experiment"] = req_args[0]
        return 0

    def apply(self):
        if self.params == None:
            raise Exception("No arguments provided")

        rval, response = self.xmlrpc.do_method(
            "portal", "modifyExperiment", self.params
        )
        return (rval, response)

    def usage(self):
        print("Usage: modifyExperiment <options> --bindings json <profile>")
        print("where:")
        print(" -a urn       - Override default aggregate URN")
        print("experiment    - Either UUID or pid,name")
        return

    pass


#
# Terminate a portal experiment
#
class terminateExperiment:
    def __init__(self, xmlrpc, params=None):
        self.xmlrpc = xmlrpc
        self.params = params
        pass

    def parseArgs(self, argv):
        self.params = {}

        try:
            opts, req_args = getopt.getopt(argv, "h", ["help"])
            pass
        except getopt.error as e:
            print(e.args[0])
            self.usage()
            return -1

        for opt, val in opts:
            if opt in ("-h", "--help"):
                self.usage()
                return 1
            pass

        # Do this after so --help is seen.
        if len(req_args) != 1:
            self.usage()
            return -1

        self.params["experiment"] = req_args[0]
        return 0

    def apply(self):
        if self.params == None:
            raise Exception("No arguments provided")

        rval, response = self.xmlrpc.do_method(
            "portal", "terminateExperiment", self.params
        )
        return (rval, response)

    def usage(self):
        print("Usage: terminateExperiment <options> <experiment>")
        print("where:")
        print("experiment     - Either UUID or pid,name")
        return

    pass


#
# Extend a portal experiment
#
class extendExperiment:
    def __init__(self, xmlrpc, params=None):
        self.xmlrpc = xmlrpc
        self.params = params
        pass

    def parseArgs(self, argv):
        self.params = {}

        try:
            opts, req_args = getopt.getopt(argv, "hm:f:", ["help"])
            pass
        except getopt.error as e:
            print(e.args[0])
            self.usage()
            return -1

        reason = ""
        for opt, val in opts:
            if opt in ("-h", "--help"):
                self.usage()
                return 1
            elif opt == "-m":
                reason = val
                pass
            elif opt == "-f":
                try:
                    reason = open(val).read()
                    pass
                except:
                    print("Could not open file: " + val)
                    return -1
            pass

        # Do this after so --help is seen.
        if len(req_args) != 2:
            self.usage()
            return -1

        self.params["experiment"] = req_args[0]
        self.params["wanted"] = req_args[1]
        self.params["reason"] = reason
        return 0

    def apply(self):
        if self.params == None:
            raise Exception("No arguments provided")

        rval, response = self.xmlrpc.do_method(
            "portal", "extendExperiment", self.params
        )
        return (rval, response)

    def usage(self):
        print("Usage: extendExperiment <options> <experiment> <hours>")
        print("where:")
        print(" -m str        - Your reason for the extension (a string)")
        print(" -f file       - A file containing your reason")
        print("experiment     - Either UUID or pid,name")
        print("hours          - Number of hours to extend")
        return

    pass


#
# Get status for a portal experiment
#
class experimentStatus:
    def __init__(self, xmlrpc, params=None):
        self.xmlrpc = xmlrpc
        self.params = params
        pass

    def parseArgs(self, argv):
        self.params = {}

        try:
            opts, req_args = getopt.getopt(argv, "hjrk", ["help"])
            pass
        except getopt.error as e:
            print(e.args[0])
            self.usage()
            return -1

        for opt, val in opts:
            if opt in ("-h", "--help"):
                self.usage()
                return 1
            elif opt == "-j":
                self.params["asjson"] = 1
                pass
            elif opt == "-k":
                params["withcert"] = 1
                pass
            elif opt == "-r":
                params["refresh"] = 1
                pass
            pass

        # Do this after so --help is seen.
        if len(req_args) != 1:
            self.usage()
            return -1

        self.params["experiment"] = req_args[0]
        return 0

    def apply(self):
        if self.params == None:
            raise Exception("No arguments provided")
        
        rval,response = self.xmlrpc.do_method("portal",
                                              "experimentStatus", self.params)
        # json_data = json.loads(response.output)
        # response.output = json_data["uuid"]
        return (rval,response)

    def usage(self):
        print("Usage: experimentStatus <options> <experiment>")
        print("where:")
        print(" -j            - json string instead of text")
        print(" -k            - include instance cert/key pair (with -j)")
        print("experiment     - Either UUID or pid,name")
        return

    pass


#
# Get manifests for a portal experiment
#
class experimentManifests:
    def __init__(self, xmlrpc, params=None):
        self.xmlrpc = xmlrpc
        self.params = params
        pass

    def parseArgs(self, argv):
        self.params = {}

        try:
            opts, req_args = getopt.getopt(argv, "h", ["help"])
            pass
        except getopt.error as e:
            print(e.args[0])
            self.usage()
            return -1

        for opt, val in opts:
            if opt in ("-h", "--help"):
                self.usage()
                return 1
            pass

        # Do this after so --help is seen.
        if len(req_args) != 1:
            self.usage()
            return -1

        self.params["experiment"] = req_args[0]
        return 0

    def apply(self):
        if self.params == None:
            raise Exception("No arguments provided")

        rval, response = self.xmlrpc.do_method(
            "portal", "experimentManifests", self.params
        )
        return (rval, response)

    def usage(self):
        print("Usage: experimentManifests <options> <experiment>")
        print("where:")
        print("experiment     - Either UUID or pid,name")
        return

    pass


#
# Reboot nodes in a portal experiment
#
class experimentReboot:
    def __init__(self, xmlrpc, params=None):
        self.xmlrpc = xmlrpc
        self.params = params
        pass

    def parseArgs(self, argv):
        self.params = {}

        try:
            opts, req_args = getopt.getopt(argv, "hf", ["help"])
            pass
        except getopt.error as e:
            print(e.args[0])
            self.usage()
            return -1

        for opt, val in opts:
            if opt in ("-h", "--help"):
                self.usage()
                return 0
            elif opt == "-f":
                self.params["power"] = 1
                pass
            pass

        # Do this after so --help is seen.
        if len(req_args) < 2:
            self.usage()
            return -1

        self.params["experiment"] = req_args.pop(0)
        self.params["nodes"] = ",".join(req_args)
        return 0

    def apply(self):
        if self.params == None:
            raise Exception("No arguments provided")

        rval, response = self.xmlrpc.do_method("portal", "reboot", self.params)
        return (rval, response)

    def usage(self):
        print("Usage: experimentReboot <options> <experiment> node [node ...]")
        print("where:")
        print(" -f            - power cycle instead of reboot")
        print("experiment     - Either UUID or pid,name")
        print("node           - List of node client ids to reboot")
        return

    pass


#
# Connect one experiment's shared vlan to another experiment's shared vlan.
#
class connectExperiment:
    def __init__(self, xmlrpc, params=None):
        self.xmlrpc = xmlrpc
        self.params = params

    def parseArgs(self, argv):
        self.params = {}

        try:
            opts, req_args = getopt.getopt(argv, "h", ["help"])
        except getopt.error as e:
            print(e.args[0])
            self.usage()
            return -1

        for opt, val in opts:
            if opt in ("-h", "--help"):
                self.usage()
                return 0

        # Do this after so --help is seen.
        if len(req_args) < 4:
            self.usage()
            return -1

        self.params["experiment"] = req_args.pop(0)
        self.params["sourcelan"] = req_args.pop(0)
        self.params["targetexp"] = req_args.pop(0)
        self.params["targetlan"] = req_args.pop(0)
        return 0

    def apply(self):
        if self.params == None:
            raise Exception("No arguments provided")

        rval, response = self.xmlrpc.do_method(
            "portal", "connectSharedLan", self.params
        )
        return (rval, response)

    def usage(self):
        print(
            "Usage: connectExperiment <experiment> <sourcelan> <target-experiment> <target-shared-vlan>"
        )
        print("where:")
        print("experiment         - Either UUID or pid,name")
        print("sourcelan          - source shared vlan name")
        print("target-experiment  - target experiment (pid,name or UUID)")
        print("target-shared-vlan - target shared vlan name")


#
# Disconnect one experiment's shared vlan to another experiment's shared vlan.
#
class disconnectExperiment:
    def __init__(self, xmlrpc, params=None):
        self.xmlrpc = xmlrpc
        self.params = params

    def parseArgs(self, argv):
        self.params = {}

        try:
            opts, req_args = getopt.getopt(argv, "h", ["help"])
        except getopt.error as e:
            print(e.args[0])
            self.usage()
            return -1

        for opt, val in opts:
            if opt in ("-h", "--help"):
                self.usage()
                return 0

        # Do this after so --help is seen.
        if len(req_args) < 2:
            self.usage()
            return -1

        self.params["experiment"] = req_args.pop(0)
        self.params["sourcelan"] = req_args.pop(0)
        return 0

    def apply(self):
        if self.params == None:
            raise Exception("No arguments provided")

        rval, response = self.xmlrpc.do_method(
            "portal", "disconnectSharedLan", self.params
        )
        return (rval, response)

    def usage(self):
        print("Usage: disconnectExperiment <experiment> <sourcelan>")
        print("where:")
        print("experiment         - Either UUID or pid,name")
        print("sourcelan          - source shared vlan name")


Handlers = {
    "startExperiment": {"help": "Start a Portal experiment", "class": startExperiment},
    "terminateExperiment": {
        "help": "Terminate a Portal experiment",
        "class": terminateExperiment,
    },
    "experimentStatus": {
        "help": "Get status for a Portal experiment",
        "class": experimentStatus,
    },
    "extendExperiment": {
        "help": "Extend a Portal experiment",
        "class": extendExperiment,
    },
    "experimentManifests": {
        "help": "Get manifests for a Portal experiment",
        "class": experimentManifests,
    },
    "experimentReboot": {
        "help": "Reboot nodes in a Portal experiment",
        "class": experimentReboot,
    },
    "connectExperiment": {
        "help": "Connect experiment to another via shared vlan",
        "class": connectExperiment,
    },
    "disconnectExperiment": {
        "help": "Disconnect experiment from another's shared vlan",
        "class": disconnectExperiment,
    },
}

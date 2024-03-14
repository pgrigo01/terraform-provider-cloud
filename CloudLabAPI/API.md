#### API Reference

This document describes the API. The command line interface scripts have
their own usage help (-h), but in order to use the api module in a python
program, you need to know how to construct the parameter dictionary that
is specific to each entry point.

Please take a look at [src/example.py](src/example.py) for a quick overview
of how to use the API. [src/workflow.py](src/workflow.py) is a more realistic
demonstration that starts an experiment, waits for an execute service to
finish, and then terminates the experiment.

The API methods described below all take a python dictionary of parameters,
and return both a result code and the raw result as an ```EmulabResponse```
object (see [src/emulab_sslxmlrpc/xmlrpc.py](src/emulab_sslxmlrpc/xmlrpc.py)).

The result codes are:

    import emulab_sslxmlrpc.xmlrpc as xmlrpc

    RESPONSE_SUCCESS 
    RESPONSE_BADARGS 
    RESPONSE_ERROR
    RESPONSE_FORBIDDEN
    RESPONSE_BADVERSION
    RESPONSE_SERVERERROR
    RESPONSE_TOOBIG
    RESPONSE_REFUSED
    RESPONSE_TIMEDOUT
    RESPONSE_SEARCHFAILED
    RESPONSE_ALREADYEXISTS
	
If an error is returned, ```response.output``` is an error message that can
be printed. 

#### startExperiment

To start an experiment, you need to provide the name of a profile, the
project to start the experiment in, and the name to use for the new
experiment. The profile is named by either its UUID or ```project,name```
(project the profile resides in, and the name of the profile). You must
have permission to use the profile, and you must belong to the project you
want to start the experiment in. For example:

	params = {
       "profile" : "PortalProfiles,small-lan",
       "proj"    : "myproject",
       "name"    : "goofyname"
    }
    (exitval,response) = api.startExperiment(rpc, params).apply();
	
There are a number of optional params:

  * **aggregate**: Override default aggregate with the provided URN,
  * **duration**: Number of ours for initial expiration,
  * **start**: Schedule experiment to start later, using a UNIX time stamp
    or date string,
  * **stop**: Schedule experiment to stop later, using a UNIX time stamp or
    date string,
  * **refspec**: refspec[:hash] of a repo based profile to use.
  * **paramset**: uid,name of a parameter set to apply,
  * **bindings**: json string of bindings to apply to profile parameters,

#### terminateExperiment

To terminate an experiment, only the experiment name is required, 
in ```project,name``` format:

	params = {
       "experiment" : "myproject,goofyname"
    }
    (exitval,response) = api.terminateExperiment(rpc, params).apply();
	
#### experimentStatus

The status of an experiment is returned as a json string, which can
be converted to a python dictionary:

	params = {
       "experiment" : "myproject,goofyname"
       "asjson"     : True
    }
    (exitval,response) = api.experimentStatus(rpc, params).apply();

    status = json.loads(response.value)

The status dictionary contains a status string (```status["status"]```), 
you  would typically wait for the status to be one of ```ready``` 
or```failed```. ```status["expires"]``` is a GMT date when the experiment
will automatically terminated unless you extend it. 

If the profile includes an ```execute``` service, there are additional
details in the status dictionary:

    {
	    "status" : "ready",
		"execute_status" : {
			"total"    : 1,
			"running"  : 0,
		    "finished" : 1,
			"failed"   : 0
		}
	}
	
#### modifyExperiment

To modify an experiment, supply a new bindings string and the experiment name.

	params = {
       "experiment" : "myproject,goofyname",
	   "bindings"   : '{"count" : "1"}'
    }
    (exitval,response) = api.modifyExperiment(rpc, params).apply();
	
#### experimentManifests

The manifests for each aggregate in the experiment can be accessed
via ```experimentManifests```:

	params = {
       "experiment" : "myproject,goofyname"
    }
    (exitval,response) = api.experimentManifests(rpc, params).apply();

    manifests = json.loads(response.value)
	
The response value is a dictionary manifests in XML format, one per
aggregate.
	
#### extendExperiment

To extend an experiment, you need the experiment name as described above,
and the number of hours you would like to extend it for. You must also
provide a reason for the extension:

	params = {
       "experiment" : "myproject,goofyname"
	   "wanted"     : 24,
	   "reason"     : "I need this for another day please"
    }
    (exitval,response) = api.extendExperiment(rpc, params).apply();
	
If the call fails, the most likely error code is ```GENIRESPONSE_REFUSED```,
the status output string will provide more details. You should then ask
for the ```experimentStatus``` to find out what the new expiration time is.
If it is less then what you asked for, an administrator must approve the
remainder.

import json
import time
from flask import Flask, request
from CloudLabAPI.src.emulab_sslxmlrpc import xmlrpc
from CloudLabAPI.src.emulab_sslxmlrpc.client import api
from db import Vlan, db

app = Flask(__name__)


@app.route('/test', methods=['GET'])
def test():
    return "Server is working!"



import tempfile
import json

RESPONSE_SUCCESS = 0
RESPONSE_BADARGS = 1
RESPONSE_ERROR = 2
RESPONSE_FORBIDDEN = 3
RESPONSE_BADVERSION = 4
RESPONSE_SERVERERROR = 5
RESPONSE_TOOBIG = 6
RESPONSE_REFUSED = 7
RESPONSE_TIMEDOUT = 8
RESPONSE_SEARCHFAILED = 12
RESPONSE_ALREADYEXISTS = 17

ERRORMESSAGES = {
    RESPONSE_SUCCESS: ('OK', 200),
    RESPONSE_BADARGS: ('Bad Arguments', 400),
    RESPONSE_ERROR: ('Something went wrong', 500),
    RESPONSE_FORBIDDEN: ('Forbidden', 403),
    RESPONSE_BADVERSION: ('Wrong Version', 505),
    RESPONSE_SERVERERROR: ('Server Error', 500),
    RESPONSE_TOOBIG: ('Too Big', 400),
    RESPONSE_REFUSED: ('Emulab is down, please try again', 500),
    RESPONSE_TIMEDOUT: ('Request Timeout', 408),
    RESPONSE_SEARCHFAILED: ('No such instance', 404),
    RESPONSE_ALREADYEXISTS: ('Already Exists', 400),
}



def parseArgs(request):
    # Check if the 'file' key is in the request files
    if 'file' not in request.files:
        return None, ("No file provided", 400)

    file = request.files['file']
    if file.filename == '':
        return None, ("No file selected", 400)

    # Save the uploaded file temporarily
    temp_file = tempfile.NamedTemporaryFile(delete=False)
    temp_file.write(file.read())
    temp_file_path = temp_file.name
    temp_file.close()

    # Parse other form parameters
    params = {}
    for key, value in request.form.items():
        if key != 'bindings':
            params[key] = value
        else:
            try:
                params[key] = json.loads(value)  # Parse JSON
            except json.JSONDecodeError:
                return None, ("Invalid bindings JSON", 400)

    return (temp_file_path, params), ("", 200)

@app.route('/experiment', methods=['POST'])
def startExperiment():
    app.logger.info("startExperiment")

    # Parse request arguments
    app.logger.info('Parsing Arguments')
    args, err = parseArgs(request)
    errVal, errCode = err
    if errCode != 200:
        return err
    file, params = args

    # Validate required parameters
    if 'proj' not in params or 'profile' not in params or 'name' not in params:
        return "Missing required parameters: proj, profile, and name.", 400

    # **Place here: Concatenate project and profile**
    # Format the profile using project and profile name
    project_profile = f"{params['proj']},{params['profile']}"  # Ensure profile contains the name, not UUID
    params['profile'] = project_profile

    # Log final parameters (for debugging)
    app.logger.info(f"Final parameters sent to CloudLab API: {params}")

    config = {
        "debug": 0,
        "impotent": 0,
        "verify": 0,
        "certificate": file,
    }
    app.logger.info(f"Server configuration: {config}")
    server = xmlrpc.EmulabXMLRPC(config)

    createdVlans = []
    app.logger.info('Checking vlans')

    bindings = params.get('bindings', {})
    sharedVlans = bindings.get('sharedVlans', []) if isinstance(bindings, dict) else []

    for vlan in sharedVlans:
        vlan_name = vlan.get('name', None)
        if not vlan_name:
            return "VLAN name is missing in bindings.", 400

        dbVlan = Vlan.filterByName(vlan_name)
        if dbVlan is None:
            app.logger.info(f"Experiment {params['name']} will create vlan {vlan_name}")
            vlan['createSharedVlan'] = "true"
            newDbVlan = Vlan(vlan_name, params['name'], False)
            newDbVlan.save()
            createdVlans.append(newDbVlan)
        else:
            app.logger.info(f"Experiment {params['name']} will use existing vlan {vlan_name}")
            while not dbVlan.ready:
                app.logger.info(f"Experiment {params['name']} waiting for {vlan_name} to be ready")
                dbVlan = dbVlan.updateFromCloudlabAndDB(app, server, params['proj'])
                if dbVlan is not None and dbVlan.ready:
                    vlan['connectSharedVlan'] = "true"
                    app.logger.info(f"VLAN {vlan_name} is ready")
                else:
                    break
                time.sleep(2)
            if dbVlan:
                dbVlan.save()

    app.logger.info('Starting Experiment')
    if 'bindings' in params:
        params['bindings'] = json.dumps(params['bindings'])  # Convert bindings back to JSON

    # Log experiment parameters
    app.logger.info(f"Experiment parameters: {params}")

    (exitval, response) = api.startExperiment(server, params).apply()
    app.logger.info(f"ExitVal: {exitval}")
    app.logger.info(f"Response: {response}")

    if exitval == 0:
        experiment_data = {
            "name": params['name'],
            "profile": params['profile'],
            "project": params['proj'],
            "vlans": [vlan.name for vlan in createdVlans]
        }
        experiment_ref = db.collection('experiments').document(params['name'])
        experiment_ref.set(experiment_data)
    else:
        for vlan in createdVlans:
            vlan.delete()

    if exitval in ERRORMESSAGES:
        return ERRORMESSAGES[exitval]

    return {"exitval": exitval, "response": response.output if exitval == 0 else "Experiment failed."}, 200 if exitval == 0 else 500


if __name__ == '__main__':
    for rule in app.url_map.iter_rules():
        print(f"Route: {rule.endpoint}, URL: {rule}")
    app.run(debug=True, port=8080, host='0.0.0.0')


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

    if 'proj' not in params or 'profile' not in params or 'name' not in params:
        return "Missing required parameters: proj, profile, and name.", 400

    # Concatenate project and profile as required by CloudLab
    project_profile = f"{params['proj']},{params['profile']}"

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
            # Save reused VLAN to Firebase
            if dbVlan:
                dbVlan.save()

    app.logger.info('Starting Experiment')
    if 'bindings' in params:
        params['bindings'] = json.dumps(params['bindings'])  # Convert bindings back to JSON
    params['profile'] = project_profile  # Use the concatenated project and profile

    app.logger.info(f"Experiment parameters: {params}")
    (exitval, response) = api.startExperiment(server, params).apply()
    app.logger.info(f"ExitVal: {exitval}")
    app.logger.info(f"Response: {response}")

    if exitval == 0:
        # Save experiment metadata to Firebase on success
        experiment_data = {
            "name": params['name'],
            "profile": params['profile'],
            "project": params['proj'],
            "vlans": [vlan.name for vlan in createdVlans]
        }
        experiment_ref = db.collection('experiment').document(params['name'])
        experiment_ref.set(experiment_data)
    else:
        # Clean up created VLANs if the experiment fails
        for vlan in createdVlans:
            vlan.delete()

    if exitval in ERRORMESSAGES:
        return ERRORMESSAGES[exitval]

    return {"exitval": exitval, "response": response.output if exitval == 0 else "Experiment failed."}, 200 if exitval == 0 else 500

@app.route('/experiment', methods=['GET'])
def experimentStatus():
    app.logger.info("experimentStatus")

    # Parse request arguments
    app.logger.info('Parsing Arguments')
    args, err = parseArgs(request)
    errVal, errCode = err
    if errCode != 200:
        return err
    file, params = args

    # Validate required parameters
    if 'proj' not in params or 'name' not in params:
        return "Missing required parameters: proj and name.", 400

    # Format the project and experiment name as required by CloudLab
    params['experiment'] = f"{params['proj']},{params['name']}"

    # Server configuration for CloudLab
    config = {
        "debug": 0,
        "impotent": 0,
        "verify": 0,
        "certificate": file,
    }
    app.logger.info(f"Server configuration: {config}")
    server = xmlrpc.EmulabXMLRPC(config)

    app.logger.info(f"Fetching status for experiment: {params['experiment']}")
    (exitval, response) = api.experimentStatus(server, params).apply()

    app.logger.info(f"ExitVal: {exitval}")
    app.logger.info(f"Response: {response}")

    # Check the response and return appropriate status
    if exitval == RESPONSE_SUCCESS:
        return {"status": "success", "data": response.output}, 200
    elif exitval in ERRORMESSAGES:
        return {"status": "error", "message": ERRORMESSAGES[exitval][0]}, ERRORMESSAGES[exitval][1]

    return {"status": "error", "message": "Unknown error occurred."}, 500


@app.route('/experiment', methods=['DELETE'])
def terminateExperiment():
    app.logger.info("terminateExperiment")

    # Parse request arguments
    app.logger.info('Parsing Arguments')
    args, err = parseArgs(request)
    errVal, errCode = err
    if errCode != 200:
        return err
    file, params = args

    # Validate required parameters
    if 'proj' not in params or 'name' not in params:
        return "Missing required parameters: proj and name.", 400

    # Format the experiment identifier as required by CloudLab (pid,name)
    params['experiment'] = f"{params['proj']},{params['name']}"

    # Server configuration for CloudLab
    config = {
        "debug": 0,
        "impotent": 0,
        "verify": 0,
        "certificate": file,
    }
    app.logger.info(f"Server configuration: {config}")
    server = xmlrpc.EmulabXMLRPC(config)

    app.logger.info(f"Terminating experiment: {params['experiment']}")
    (exitval, response) = api.terminateExperiment(server, params).apply()

    app.logger.info(f"ExitVal: {exitval}")
    app.logger.info(f"Response: {response}")

    # Check the response and handle errors
    if exitval == RESPONSE_SUCCESS:
        # Delete the corresponding record in Firebase
        try:
            experiment_ref = db.collection('experiment').document(params['name'])
            experiment_ref.delete()
            app.logger.info(f"Firebase record for experiment '{params['name']}' deleted successfully.")
        except Exception as e:
            app.logger.error(f"Failed to delete Firebase record: {e}")
            return {
                "status": "success",
                "message": "Experiment terminated, but failed to delete Firebase record."
            }, 200

        return {"status": "success", "message": "Experiment terminated successfully."}, 200
    elif exitval in ERRORMESSAGES:
        return {"status": "error", "message": ERRORMESSAGES[exitval][0]}, ERRORMESSAGES[exitval][1]

    return {"status": "error", "message": "Unknown error occurred during termination."}, 500

# @app.route('/experiments', methods=['GET'])
# def getExperiments():
#     # Get query parameters (if any)
#     project = request.args.get('proj', None)  # Optional query parameter for filtering by project

#     try:
#         app.logger.info(f"Fetching experiments. Project filter: {project if project else 'None'}")
#         experiments = []

#         if project:
#             # Query for experiments matching the specified project
#             docs = db.collection('experiment').where('project', '==', project).stream()
#         else:
#             # Fetch all experiments if no project filter is provided
#             docs = db.collection('experiment').stream()

#         for doc in docs:
#             experiment_data = doc.to_dict()
#             experiment_data['id'] = doc.id  # Include document ID for reference
#             experiments.append(experiment_data)

#         return {"status": "success", "experiments": experiments}, 200

#     except Exception as e:
#         app.logger.error(f"Error fetching experiments: {e}")
#         return {"status": "error", "message": "Failed to fetch experiments."}, 500


@app.route('/experiments', methods=['GET'])
def getExperiments():
    # Check if it's a GET request
    if request.method == 'GET':
        # Get query parameters
        project = request.args.get('proj', None)  # Optional parameter for filtering by project

        try:
            app.logger.info(f"Fetching experiments. Project filter: {project if project else 'None'}")
            experiments = []

            # Retrieve documents from Firebase
            if project:
                # Filter experiments by project
                docs = db.collection('experiment').where('project', '==', project).stream()
            else:
                # Get all experiments if no filter is applied
                docs = db.collection('experiment').stream()

            # Process each document
            for doc in docs:
                experiment_data = doc.to_dict()
                experiment_data['id'] = doc.id  # Include document ID
                experiments.append(experiment_data)

            return {"status": "success", "experiments": experiments}, 200

        except Exception as e:
            app.logger.error(f"Error fetching experiments: {e}")
            return {"status": "error", "message": "Failed to fetch experiments."}, 500
    else:
        # Return an error for unsupported methods
        return {"status": "error", "message": "Unsupported HTTP method for this route."}, 405



@app.route('/experiments/filter', methods=['GET'])
def filterExperimentsByPrefix():
    # Get the prefix from query parameters
    prefix = request.args.get('prefix', None)
    if not prefix:
        return {"status": "error", "message": "Missing required parameter: prefix"}, 400

    try:
        app.logger.info(f"Fetching experiments with prefix: {prefix}")
        experiments = []

        # Query experiments with names that start with the given prefix
        docs = db.collection('experiment')\
            .where('name', '>=', prefix)\
            .where('name', '<', prefix + '\uffff')\
            .stream()

        for doc in docs:
            experiment_data = doc.to_dict()
            experiment_data['id'] = doc.id  # Include document ID
            experiments.append(experiment_data)

        return {"status": "success", "experiments": experiments}, 200

    except Exception as e:
        app.logger.error(f"Error filtering experiments: {e}")
        return {"status": "error", "message": "Failed to filter experiments."}, 500



if __name__ == '__main__':
    for rule in app.url_map.iter_rules():
        print(f"Route: {rule.endpoint}, URL: {rule}")
    app.run(debug=True, port=8080, host='0.0.0.0')
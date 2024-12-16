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


@app.before_request
def log_request():
    app.logger.info(f"Received {request.method} request to {request.url}")
    app.logger.info(f"Headers: {request.headers}")
    if request.is_json:
        app.logger.info(f"JSON Payload: {request.get_json()}")
    elif request.form:
        app.logger.info(f"Form Data: {request.form}")
    else:
        app.logger.info(f"Raw Data: {request.data}")


@app.route('/experiment', methods=['POST'])
def startExperiment():
    app.logger.info("startExperiment")

    # Parse Arguments
    app.logger.info('Parsing Arguments')
    args, err = parseArgs(request)
    errVal, errCode = err
    if errCode != 200:
        return {"error": errVal}, errCode
    file, params = args

    # Validate required parameters
    required_params = ['proj', 'profile', 'name']
    missing_params = [p for p in required_params if p not in params]
    if missing_params:
        return {"error": f"Missing required parameters: {', '.join(missing_params)}"}, 400

        # Fix experiment and profile parameters
    experiment_name = params['name'].strip('"')  # Ensure any surrounding quotes are removed
    params['experiment'] = f"{params['proj']},{experiment_name}"
    params['name'] = experiment_name  # Update the 'name' field as well

    params['experiment'] = f"{params['proj']},{experiment_name}"
    params['profile'] = params['profile'].strip()  # Ensure profile is clean

    # Rebuild bindings if necessary
    if 'bindings' in params:
        try:
            # Check if bindings is already a dictionary
            if isinstance(params['bindings'], str):
                bindings = json.loads(params['bindings'])  # Parse bindings JSON
            elif isinstance(params['bindings'], dict):
                bindings = params['bindings']  # Use it directly if it's already a dictionary
            else:
                raise TypeError("Bindings must be a JSON string or dictionary.")

            # Update bindings with additional required fields
            bindings.update({
                "experiment": experiment_name,
                "profile": params['profile'],
                "proj": params['proj']
            })

            params['bindings'] = json.dumps(bindings)  # Convert back to JSON
        except json.JSONDecodeError:
            return {"error": "Invalid JSON in bindings."}, 400
        except TypeError as e:
            app.logger.error(f"Bindings error: {e}")
            return {"error": str(e)}, 400

    app.logger.info(f"Experiment parameters: {params}")

    # CloudLab API configuration
    config = {
        "debug": 0,
        "impotent": 0,
        "verify": 0,
        "certificate": file,
    }
    app.logger.info(f"Server configuration: {config}")
    server = xmlrpc.EmulabXMLRPC(config)

    # Check VLANs
    created_vlans = []
    if 'bindings' in params and isinstance(bindings := json.loads(params['bindings']), dict):
        shared_vlans = bindings.get('sharedVlans', [])
        for vlan in shared_vlans:
            vlan_name = vlan.get('name')
            if not vlan_name:
                return {"error": "VLAN name is missing in bindings."}, 400

            db_vlan = Vlan.filter_by_name(vlan_name)
            if db_vlan is None:
                app.logger.info(f"Creating VLAN '{vlan_name}' for experiment '{experiment_name}'")
                vlan['createSharedVlan'] = "true"
                new_vlan = Vlan(vlan_name, experiment_name, False)
                new_vlan.save()
                created_vlans.append(new_vlan)
            else:
                app.logger.info(f"Using existing VLAN '{vlan_name}' for experiment '{experiment_name}'")
                while not db_vlan.ready:
                    app.logger.info(f"Waiting for VLAN '{vlan_name}' to become ready")
                    db_vlan = db_vlan.update_from_cloudlab_and_db(app, server, params['proj'])
                    if db_vlan and db_vlan.ready:
                        vlan['connectSharedVlan'] = "true"
                        app.logger.info(f"VLAN '{vlan_name}' is ready")
                        break
                    time.sleep(2)
                if db_vlan:
                    db_vlan.save()  # Save updated state

    # Start the experiment
    app.logger.info("Starting Experiment")
    exitval, response = api.startExperiment(server, params).apply()
    app.logger.info(f"ExitVal: {exitval}")
    app.logger.info(f"Response: {response}")

    # Handle experiment creation results
    if exitval == 0:
        # Save experiment metadata to Firebase
        try:
            experiment_data = {
                "name": experiment_name,
                "profile": params['profile'],
                "project": params['proj'],
                "vlans": [vlan.name for vlan in created_vlans],
                "status": "running"
            }
            db.collection('experiment').document(experiment_name).set(experiment_data)
            app.logger.info(f"Experiment '{experiment_name}' metadata saved to Firebase.")
        except Exception as e:
            app.logger.error(f"Failed to save experiment metadata to Firebase: {e}")
    else:
        # Cleanup created VLANs if the experiment fails
        for vlan in created_vlans:
            vlan.delete()

    if exitval in ERRORMESSAGES:
        return {"error": ERRORMESSAGES[exitval][0]}, ERRORMESSAGES[exitval][1]

    return {
        "exitval": exitval,
        "response": response.output if exitval == 0 else "Experiment failed."
    }, 200 if exitval == 0 else 500
 


@app.route('/experiment', methods=['GET'])
def experimentStatus():
    app.logger.info("experimentStatus")

    # Parse request arguments
    app.logger.info('Parsing Arguments')
    args, err = parseArgs(request)
    errVal, errCode = err
    if errCode != 200:
        return {"error": errVal}, errCode
    file, params = args

    # Validate required parameters
    if 'proj' not in params or 'experiment' not in params:
        return {"error": "Missing required parameters: proj or experiment."}, 400

    # Fix experiment parameter
    experiment_name = params['experiment'].strip('"')
    params['experiment'] = f"{params['proj']},{experiment_name}"

    # CloudLab server configuration
    config = {
        "debug": 0,
        "impotent": 0,
        "verify": 0,
        "certificate": file,
    }
    app.logger.info(f"Server configuration: {config}")
    server = xmlrpc.EmulabXMLRPC(config)

    app.logger.info(f"Fetching status for experiment: {params['experiment']}")
    exitval, response = api.experimentStatus(server, params).apply()

    app.logger.info(f"ExitVal: {exitval}")
    app.logger.info(f"Response: {response}")

    # Return response based on exitval
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
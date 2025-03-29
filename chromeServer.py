import getpass
import json
import re
import time
from io import BytesIO
from datetime import datetime, timezone
import tempfile
import os
import csv
import math
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, request, jsonify, Request
import CloudLabAPI.src.emulab_sslxmlrpc.client.api as api
import CloudLabAPI.src.emulab_sslxmlrpc.xmlrpc as xmlrpc

# Local modules used for experiment management and extension
import experimentCollector
import firefox
from algorithmExpExtension import extendAllExperimentsToLast

# --------------------------
# Flask App and Logger Setup
# --------------------------
app = Flask(__name__)
app.logger.setLevel('INFO')

# --------------------------
# Error / Status Constants
# --------------------------
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
    RESPONSE_ALREADYEXISTS: ('Already Exists', 400)
}

# -------------------------------------------------------------------
# Helper Functions for Flask Endpoints
# -------------------------------------------------------------------
def is_valid_json(json_str):
    try:
        _ = json.loads(json_str)
        return True
    except json.JSONDecodeError:
        return False

def json_to_dict(json_string):
    return json.loads(json_string)

def dict_to_json(dictionary):
    return json.dumps(dictionary)

def parseArgs(req: Request):
    if 'file' not in req.files:
        return (), ("No file provided", 400)
    file = req.files['file']
    if file.filename == '':
        return (), ("No file selected", 400)

    file_content = BytesIO()
    file.save(file_content)

    temp_file = tempfile.NamedTemporaryFile(delete=False)
    temp_file.write(file_content.getvalue())
    temp_file_path = temp_file.name
    temp_file.close()

    params = {}
    for key, value in req.form.items():
        if key != 'bindings':
            params[key] = value.replace('"', '')
        else:
            if is_valid_json(value):
                value_dict = json_to_dict(value)
                if "sharedVlans" in value_dict:
                    if isinstance(value_dict["sharedVlans"], str):
                        value_dict["sharedVlans"] = json_to_dict(value_dict["sharedVlans"])
                params[key] = value_dict
            else:
                return (), ("Invalid bindings json", 400)
    app.logger.debug(f"parseArgs -> file={temp_file_path}, params={params}")
    return (temp_file_path, params), ("", 200)

def parse_uuid_from_response(response_string: str) -> str:
    match = re.search(r"UUID:\s+([a-z0-9-]+)", response_string, re.IGNORECASE)
    if match:
        return match.group(1)
    return ""

# -------------------------------------------------------------------
# Flask API Endpoints
# -------------------------------------------------------------------
@app.route('/experiment', methods=['POST'])
def startExperiment():
    app.logger.info("startExperiment")
    args, err = parseArgs(request)
    errVal, errCode = err
    if errCode != 200:
        return err
    file, params = args
    if 'proj' not in params or 'profile' not in params:
        return "Project and/or profile param not provided", 400

    config = {
        "debug": 0,
        "impotent": 0,
        "verify": 0,
        "certificate": file,
    }
    app.logger.info(f"Server configuration: {config}")
    server = xmlrpc.EmulabXMLRPC(config)
    if 'bindings' in params and isinstance(params['bindings'], dict):
        params['bindings'] = dict_to_json(params['bindings'])
    app.logger.info(f"Experiment parameters!!!: {params}")

    max_retries = 5
    retry_delay = 3
    exitval, response = None, None
    for attempt in range(1, max_retries + 1):
        #print(params)
        (exitval, response) = api.startExperiment(server, params).apply()
        app.logger.info(f"startExperiment attempt {attempt}/{max_retries}: exitval={exitval}, response={response}")
        if exitval == 0:
            break
        else:
            app.logger.warning(
                f"startExperiment attempt {attempt} failed with exitval={exitval}. Retrying in {retry_delay} seconds..."
            )
            time.sleep(retry_delay)
    if exitval != 0:
        app.logger.error("All attempts to start experiment failed.")
        return ERRORMESSAGES.get(exitval, ERRORMESSAGES[RESPONSE_ERROR])
    cloudlab_uuid = parse_uuid_from_response(str(response))
    app.logger.info(f"Parsed UUID from startExperiment: '{cloudlab_uuid}'")
    if not cloudlab_uuid:
        app.logger.info("Could not parse UUID from startExperiment. Checking experimentStatus for the real UUID...")
        status_params = {'proj': params['proj'], 'experiment': f"{params['proj']},{params['name']}"}
        (status_exitval, status_response) = api.experimentStatus(server, status_params).apply()
        app.logger.info(f"experimentStatus exitval={status_exitval}, response={status_response}")
        if status_exitval == 0:
            cloudlab_uuid = parse_uuid_from_response(str(status_response))
            app.logger.info(f"Parsed UUID from experimentStatus: '{cloudlab_uuid}'")
        else:
            app.logger.warning("experimentStatus call failed. Storing 'unknown' for UUID.")
            cloudlab_uuid = "unknown"
    if not cloudlab_uuid:
        cloudlab_uuid = "unknown"
    app.logger.info(f"Experiment '{params.get('name', 'unnamed')}' started with UUID '{cloudlab_uuid}'.")
    return ERRORMESSAGES.get(exitval, ERRORMESSAGES[RESPONSE_ERROR])

@app.route('/experiment', methods=['GET'])
def experimentStatus():
    app.logger.info("experimentStatus")
    args, err = parseArgs(request)
    errVal, errCode = err
    if errCode != 200:
        return err
    file, params = args
    if 'proj' not in params or 'experiment' not in params:
        return "Project and/or experiment param not provided", 400
    params['experiment'] = f"{params['proj']},{params['experiment']}"
    config = {
        "debug": 0,
        "impotent": 0,
        "verify": 0,
        "certificate": file,
    }
    app.logger.info(f"Server configuration: {config}")
    server = xmlrpc.EmulabXMLRPC(config)
    max_retries = 5
    retry_delay = 2
    exitval, response = None, None
    for attempt in range(1, max_retries + 1):
        (exitval, response) = api.experimentStatus(server, params).apply()
        app.logger.info(f"Attempt {attempt}/{max_retries}, exitval={exitval}, response={response}")
        if response is not None and hasattr(response, 'output'):
            return (str(response.output), ERRORMESSAGES[exitval][1])
        app.logger.warning(
            f"experimentStatus attempt {attempt} did not return a valid response. Retrying in {retry_delay} second(s)..."
        )
        time.sleep(retry_delay)
    return ("No valid status after multiple retries", 500)

@app.route('/experiment', methods=['DELETE'])
@app.route('/experiment', methods=['DELETE'])
def terminateExperiment():
    app.logger.info("terminateExperiment")
    args, err = parseArgs(request)
    errVal, errCode = err
    if errCode != 200:
        return err
    file, params = args
    app.logger.info(f"Received params for termination: {params}")

    # --- New logic: Use UUID if provided ---
    # If a "uuid" parameter exists and is non-empty, then use it as the experiment identifier.
    if 'uuid' in params and params['uuid'].strip() != "":
        params["experiment"] = params["uuid"].strip()
        app.logger.info(f"Using UUID for termination: {params['experiment']}")
    else:
        # Otherwise, if the "experiment" field is not a UUID (e.g. no dash), use command style:
        exp = params.get("experiment", "")
        if exp == "" and "name" in params and params["name"] != "":
            exp = params["name"]
        if "-" not in exp:
            exp = f"{params['proj']},{exp}"
            params["experiment"] = exp
            app.logger.info(f"Using command-style termination: {params['experiment']}")
    # ------------------------------------------------

    config = {
        "debug": 0,
        "impotent": 0,
        "verify": 0,
        "certificate": file,
    }
    app.logger.info(f"Server configuration: {config}")
    server = xmlrpc.EmulabXMLRPC(config)
    max_retries = 5
    retry_delay = 2
    exitval, response = None, None
    for attempt in range(1, max_retries + 1):
        (exitval, response) = api.terminateExperiment(server, params).apply()
        app.logger.info(f"terminateExperiment attempt {attempt}/{max_retries}: exitval={exitval}, response={response}")
        if exitval == 0:
            break
        else:
            app.logger.warning(
                f"terminateExperiment attempt {attempt} failed with exitval={exitval}. Retrying in {retry_delay} seconds..."
            )
            time.sleep(retry_delay)
    if exitval != 0:
        app.logger.error("All attempts to terminate experiment failed.")
        return ERRORMESSAGES.get(exitval, ERRORMESSAGES[RESPONSE_ERROR])
    app.logger.info(f"Experiment termination successful for parameters: {params}.")
    return ERRORMESSAGES[exitval]

# -------------------------------------------------------------------
# Methods for Main Setup
# -------------------------------------------------------------------
def get_credentials():
    username = input("Enter CloudLab username: ").strip()
    password = getpass.getpass("Enter CloudLab password: ").strip()
    if not username or not password:
        print("Error: Username or password cannot be empty.")
        exit(1)
    return username, password

def initialize_experiments(username, password):
    app.logger.info("Initializing experiments at startup...")
    experimentCollector.getExperiments(username, password)

def setup_scheduler(username, password):
   
    scheduler = BackgroundScheduler()

    def scheduled_experiment_collector():
        app.logger.info("Running scheduled experimentCollector...")
        experimentCollector.getExperiments(username, password)

    # Schedule experiment data refresh every hour.
    scheduler.add_job(func=scheduled_experiment_collector, trigger="interval", hours=1)
    # Schedule the extension logic using the imported function from algorithmExpExtension.py.
    scheduler.add_job(func=extendAllExperimentsToLast, trigger="interval", hours=1,
                      args=[username, password, 1.0])
    scheduler.start()
    app.logger.info("Scheduler started.")
    return scheduler

def run_server():
    port = 8080
    app.run(debug=True, port=port, host='0.0.0.0', use_reloader=False)

# -------------------------------------------------------------------
# Main Entry Point
# -------------------------------------------------------------------
def main():
    global global_username, global_password
    global_username, global_password = get_credentials()
    initialize_experiments(global_username, global_password)
    setup_scheduler(global_username, global_password)
    run_server()

if __name__ == '__main__':  
    #os.environ["FLASK_ENV"] = "development"
    os.environ["FLASK_ENV"] = "info"
    main()

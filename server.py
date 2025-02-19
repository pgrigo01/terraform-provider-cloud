import json
import re
import time
from io import BytesIO
import threading
from datetime import datetime, timedelta
import tempfile

from flask import Flask, request, jsonify, Request
import CloudLabAPI.src.emulab_sslxmlrpc.client.api as api
import CloudLabAPI.src.emulab_sslxmlrpc.xmlrpc as xmlrpc

from db import db  # Firestore client

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
# Helper: Check if a string is valid JSON
# -------------------------------------------------------------------
def is_valid_json(json_str):
    try:
        _ = json.loads(json_str)
        return True
    except json.JSONDecodeError:
        return False


# -------------------------------------------------------------------
# Helper: Convert JSON string to dict
# -------------------------------------------------------------------
def json_to_dict(json_string):
    return json.loads(json_string)


# -------------------------------------------------------------------
# Helper: Convert dict to JSON string
# -------------------------------------------------------------------
def dict_to_json(dictionary):
    return json.dumps(dictionary)


# -------------------------------------------------------------------
# parseArgs: Parse the form-data for file (certificate) + params
# -------------------------------------------------------------------
def parseArgs(req: Request):
    """
    Expects:
      - file=@<path-to-cert> in req.files['file']
      - Additional text fields in req.form (e.g. proj, profile, name, etc.)
      - For "bindings", if present, expects JSON
    """
    if 'file' not in req.files:
        return (), ("No file provided", 400)

    file = req.files['file']
    if file.filename == '':
        return (), ("No file selected", 400)

    # Save file content
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
            # Attempt to parse JSON in 'bindings'
            if is_valid_json(value):
                value_dict = json_to_dict(value)
                # If there's a nested JSON string for sharedVlans, parse that too
                if "sharedVlans" in value_dict:
                    if isinstance(value_dict["sharedVlans"], str):
                        # Convert that JSON string to a dict
                        value_dict["sharedVlans"] = json_to_dict(value_dict["sharedVlans"])
                params[key] = value_dict
            else:
                return (), ("Invalid bindings json", 400)

    app.logger.debug(f"parseArgs -> file={temp_file_path}, params={params}")
    return (temp_file_path, params), ("", 200)


# -------------------------------------------------------------------
# Helper: Example function to parse UUID from any given string
# -------------------------------------------------------------------
def parse_uuid_from_response(response_string: str) -> str:
    """
    Tries to find a line like "UUID: d2a70fdc-c375-11ef-af1a-e4434b2381fc"
    and returns the captured group. If none found, returns empty.
    """
    match = re.search(r"UUID:\s+([a-z0-9-]+)", response_string, re.IGNORECASE)
    if match:
        return match.group(1)
    return ""


# -------------------------------------------------------------------
# API: Start the experiment (POST /experiment)
# - Creates doc in Firestore with 'uuid': 'unknown'
# - Immediately calls experimentStatus to fetch real UUID
# - Updates Firestore doc with the correct UUID
# -------------------------------------------------------------------
@app.route('/experiment', methods=['POST'])
def startExperiment():
    app.logger.info("startExperiment")

    # 1. Parse request arguments
    app.logger.info('Parsing Arguments')
    args, err = parseArgs(request)
    errVal, errCode = err
    if errCode != 200:
        return err
    file, params = args

    # Ensure required fields
    if 'proj' not in params or 'profile' not in params:
        return "Project and/or profile param not provided", 400

    # 2. Configure Emulab server
    config = {
        "debug": 0,
        "impotent": 0,
        "verify": 0,
        "certificate": file,
    }
    app.logger.info(f'Server configuration: {config}')
    server = xmlrpc.EmulabXMLRPC(config)

    # 3. Prepare experiment parameters
    if 'bindings' in params and isinstance(params['bindings'], dict):
        params['bindings'] = dict_to_json(params['bindings'])
    app.logger.info(f'Experiment parameters: {params}')

    # 4. Retry logic for starting the experiment
    max_retries = 5
    retry_delay = 3  # seconds
    for attempt in range(1, max_retries + 1):
        (exitval, response) = api.startExperiment(server, params).apply()
        app.logger.info(f"startExperiment attempt {attempt}/{max_retries}: exitval={exitval}, response={response}")
        if exitval == 0:
            break
        else:
            app.logger.warning(
                f"startExperiment attempt {attempt} failed with exitval={exitval}. Retrying in {retry_delay} seconds..."
            )
            time.sleep(retry_delay)

    # If all attempts failed, return an error
    if exitval != 0:
        app.logger.error("All attempts to start experiment failed.")
        return ERRORMESSAGES.get(exitval, ERRORMESSAGES[RESPONSE_ERROR])

    # 5. Try to parse the UUID from the startExperiment response
    cloudlab_uuid = parse_uuid_from_response(str(response))
    app.logger.info(f"Parsed UUID from startExperiment: '{cloudlab_uuid}'")

    # If parsing fails, call experimentStatus to get the correct UUID 
    if not cloudlab_uuid:
        app.logger.info("Could not parse UUID from startExperiment. Checking experimentStatus for the real UUID...")
        status_params = {
            'proj': params['proj'],
            'experiment': f"{params['proj']},{params['name']}"
        }
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

    # 6. Save experiment metadata to Firestore with TTL
    now = datetime.utcnow()
    expire_at = now + timedelta(hours=16)  # TTL set to 16 hours from now 

    experiment_data = {
        'name': params['name'],      # experiment name
        'uuid': cloudlab_uuid,       # CloudLab UUID
        'project': params['proj'],
        'status': 'started',
        'created_at': now,           # timestamp of creation (UTC)
        'expireAt': expire_at        # new TTL field
    }
    db.collection('experiments').document(params['name']).set(experiment_data)
    app.logger.info(f"Experiment '{params['name']}' (uuid='{cloudlab_uuid}') saved to Firestore with expireAt={expire_at}.")

    return ERRORMESSAGES.get(exitval, ERRORMESSAGES[RESPONSE_ERROR])


# -------------------------------------------------------------------
# API: experimentStatus (GET /experiment)
# -------------------------------------------------------------------
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
    app.logger.info(f'Server configuration: {config}')
    server = xmlrpc.EmulabXMLRPC(config)

    max_retries = 5
    retry_delay = 2  # seconds

    for attempt in range(1, max_retries + 1):
        (exitval, response) = api.experimentStatus(server, params).apply()
        app.logger.info(f"Attempt {attempt}/{max_retries}, exitval={exitval}, response={response}")

        # If the call succeeded and we have a response object with .output, return immediately.
        if response is not None and hasattr(response, 'output'):
            return (str(response.output), ERRORMESSAGES[exitval][1])

        # Otherwise, log a warning and retry after a short delay.
        app.logger.warning(
            f"experimentStatus attempt {attempt} did not return a valid response. "
            f"Retrying in {retry_delay} second(s)..."
        )
        time.sleep(retry_delay)

    # If we get here, all attempts failed to produce a valid response
    return ("No valid status after multiple retries", 500)

# -------------------------------------------------------------------
# API: Terminate Experiment (DELETE /experiment)
# -------------------------------------------------------------------
@app.route('/experiment', methods=['DELETE'])
def terminateExperiment():
    app.logger.info("terminateExperiment")
    args, err = parseArgs(request)
    errVal, errCode = err
    if errCode != 200:
        return err
    file, params = args

    app.logger.info(f"Received params for termination: {params}")

    config = {
        "debug": 0,
        "impotent": 0,
        "verify": 0,
        "certificate": file,
    }
    app.logger.info(f'Server configuration: {config}')
    server = xmlrpc.EmulabXMLRPC(config)

    # Terminate on CloudLab
    (exitval, response) = api.terminateExperiment(server, params).apply()
    app.logger.info(f"terminateExperiment exitval={exitval}, response={response}")

    if exitval == 0:
        uuid_to_delete = params.get('experiment') or params.get('name', '')
        app.logger.info(f"CloudLab termination successful; cleaning up doc(s) for uuid='{uuid_to_delete}' in Firestore.")

        exp_docs = db.collection('experiments').where('uuid', '==', uuid_to_delete).stream()
        exp_list = list(exp_docs)
        app.logger.info(f"Found {len(exp_list)} experiment doc(s) with uuid='{uuid_to_delete}'. Deleting...")
        for doc in exp_list:
            doc_id = doc.id
            doc.reference.delete()
            app.logger.info(f"Deleted experiment doc '{doc_id}' in Firestore.")

        return ERRORMESSAGES[exitval]
    else:
        app.logger.error("Failed to terminate on CloudLab; skipping Firestore cleanup.")
        return ERRORMESSAGES.get(exitval, ERRORMESSAGES[RESPONSE_ERROR])


# -------------------------------------------------------------------
# Listing all experiments (GET /experiments)
# -------------------------------------------------------------------
@app.route('/experiments', methods=['GET'])
def listExperiments():
    try:
        filter_name = request.args.get('name')
        filter_project = request.args.get('proj')
        filter_name_startswith = request.args.get('name_startswith')
        experiments_ref = db.collection('experiments')
        filter_uuid = request.args.get('uuid')
        filter_uuid_startswith = request.args.get('uuid_startswith')
        query = experiments_ref

        # Apply exact name filter if provided
        if filter_name:
            query = query.where('name', '==', filter_name)

        # Apply project filter if provided
        if filter_project:
            query = query.where('project', '==', filter_project)
        
        # Apply exact uuid filter if provided
        if filter_uuid:
            query = query.where('uuid', '==', filter_uuid)

        # Apply name_startswith filter if provided
        if filter_name_startswith:
            start = filter_name_startswith
            end = filter_name_startswith + u'\uf8ff'
            query = query.where('name', '>=', start).where('name', '<=', end)

        # Apply uuid_startswith filter if providedw
        if filter_uuid_startswith:
            start = filter_uuid_startswith
            end = filter_uuid_startswith + u'\uf8ff'
            query = query.where('uuid', '>=', start).where('uuid', '<=', end)
        
        experiments = query.stream()
        experiments_list = [exp.to_dict() for exp in experiments]
        return jsonify(experiments_list), 200

    except Exception as e:
        app.logger.error(f"Error listing experiments: {e}")
        return jsonify({'error': str(e)}), 500


# -------------------------------------------------------------------
# Background Task: Delete expired documents every minute
# -------------------------------------------------------------------
def delete_expired_documents():
    with app.app_context():
        now = datetime.utcnow()
        expired_docs = db.collection('experiments').where('expireAt', '<=', now).stream()
        deleted_count = 0
        for doc in expired_docs:
            doc.reference.delete()
            deleted_count += 1
            app.logger.info(f"Deleted expired document: {doc.id}")
        if deleted_count:
            app.logger.info(f"Total expired documents deleted: {deleted_count}")

def schedule_deletion():
    while True:
        delete_expired_documents()
        time.sleep(60)  # run every minute

# Start the background deletion thread
threading.Thread(target=schedule_deletion, daemon=True).start()


# -------------------------------------------------------------------
# Main entry point
# -------------------------------------------------------------------
if __name__ == '__main__':
    port = 8080
    app.run(debug=True, port=port, host='0.0.0.0')

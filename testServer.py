import json
import re
import time
from io import BytesIO
import threading
from datetime import datetime, timedelta, timezone
import tempfile
import sqlite3
import subprocess

from flask import Flask, request, jsonify, Request
import CloudLabAPI.src.emulab_sslxmlrpc.client.api as api
import CloudLabAPI.src.emulab_sslxmlrpc.xmlrpc as xmlrpc

app = Flask(__name__)
app.logger.setLevel('INFO')

# Global variables for management node and last experiment
last_experiment = None
management_node_info = None
GLOBAL_CERTIFICATE = "cloudlab-decrypted.pem"  # Update with your actual certificate path

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
# Initialize local SQLite database
# -------------------------------------------------------------------
connection = sqlite3.connect("experiments.db", check_same_thread=False)
cursor = connection.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS experiments (
    name TEXT PRIMARY KEY,
    uuid TEXT,
    project TEXT,
    status TEXT,
    created_at TEXT,
    expireAt TEXT
)
""")
connection.commit()

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

# -------------------------------------------------------------------
# Helper: Parse UUID from response string
# -------------------------------------------------------------------
def parse_uuid_from_response(response_string: str) -> str:
    match = re.search(r"UUID:\s+([a-z0-9-]+)", response_string, re.IGNORECASE)
    if match:
        return match.group(1)
    return ""

# -------------------------------------------------------------------
# API: Start the experiment (POST /experiment)
# -------------------------------------------------------------------
@app.route('/experiment', methods=['POST'])
def startExperiment():
    app.logger.info("startExperiment")
    app.logger.info('Parsing Arguments')
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
    app.logger.info(f'Server configuration: {config}')
    server = xmlrpc.EmulabXMLRPC(config)

    if 'bindings' in params and isinstance(params['bindings'], dict):
        params['bindings'] = dict_to_json(params['bindings'])
    app.logger.info(f'Experiment parameters: {params}')

    max_retries = 5
    retry_delay = 1.5
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

    if exitval != 0:
        app.logger.error("All attempts to start experiment failed.")
        return ERRORMESSAGES.get(exitval, ERRORMESSAGES[RESPONSE_ERROR])

    cloudlab_uuid = parse_uuid_from_response(str(response))
    app.logger.info(f"Parsed UUID from startExperiment: '{cloudlab_uuid}'")

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

    now = datetime.now(timezone.utc)
    expire_at = now + timedelta(hours=16)

    experiment_data = {
        'name': params['name'],
        'uuid': cloudlab_uuid,
        'project': params['proj'],
        'status': 'started',
        'created_at': now.isoformat(),
        'expireAt': expire_at.isoformat()
    }

    cursor.execute("""
        INSERT OR REPLACE INTO experiments (name, uuid, project, status, created_at, expireAt)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        experiment_data['name'],
        experiment_data['uuid'],
        experiment_data['project'],
        experiment_data['status'],
        experiment_data['created_at'],
        experiment_data['expireAt']
    ))
    connection.commit()

    app.logger.info(
        f"Experiment '{params['name']}' (uuid='{cloudlab_uuid}') saved to SQLite with expireAt={expire_at}."
    )
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
    retry_delay = 2

    for attempt in range(1, max_retries + 1):
        (exitval, response) = api.experimentStatus(server, params).apply()
        app.logger.info(f"Attempt {attempt}/{max_retries}, exitval={exitval}, response={response}")

        if response is not None and hasattr(response, 'output'):
            return (str(response.output), ERRORMESSAGES[exitval][1])

        app.logger.warning(
            f"experimentStatus attempt {attempt} did not return a valid response. "
            f"Retrying in {retry_delay} second(s)..."
        )
        time.sleep(retry_delay)

    return ("No valid status after multiple retries", 500)

# -------------------------------------------------------------------
# API: Terminate Experiment (DELETE /experiment)
# -------------------------------------------------------------------
@app.route('/experiment', methods=['DELETE'])
def terminateExperiment():
    global last_experiment
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

    (exitval, response) = api.terminateExperiment(server, params).apply()
    app.logger.info(f"terminateExperiment exitval={exitval}, response={response}")

    if exitval == 0:
        uuid_to_delete = params.get('experiment') or params.get('name', '')
        cursor.execute("SELECT name, created_at FROM experiments WHERE uuid = ?", (uuid_to_delete,))
        row = cursor.fetchone()
        if row:
            exp_name, created_at = row
            now = datetime.now(timezone.utc)
            duration = now - datetime.fromisoformat(created_at)
            last_experiment = {
                'name': exp_name,
                'created_at': created_at,
                'terminated_at': now.isoformat(),
                'duration': duration.total_seconds()
            }
        cursor.execute("SELECT name FROM experiments WHERE uuid = ?", (uuid_to_delete,))
        rows = cursor.fetchall()
        if rows:
            for row in rows:
                exp_name = row[0]
                cursor.execute("DELETE FROM experiments WHERE name = ?", (exp_name,))
            connection.commit()
            app.logger.info(f"Deleted experiment record(s) for uuid='{uuid_to_delete}'.")
        else:
            app.logger.info(f"No experiment record found for uuid='{uuid_to_delete}'.")
        return ERRORMESSAGES[exitval]
    else:
        app.logger.error("Failed to terminate on CloudLab; skipping local SQLite cleanup.")
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
        filter_uuid = request.args.get('uuid')
        filter_uuid_startswith = request.args.get('uuid_startswith')

        query = "SELECT name, uuid, project, status, created_at, expireAt FROM experiments WHERE 1=1"
        q_params = []

        if filter_name:
            query += " AND name = ?"
            q_params.append(filter_name)
        if filter_project:
            query += " AND project = ?"
            q_params.append(filter_project)
        if filter_uuid:
            query += " AND uuid = ?"
            q_params.append(filter_uuid)
        if filter_name_startswith:
            query += " AND name LIKE ?"
            q_params.append(filter_name_startswith + "%")
        if filter_uuid_startswith:
            query += " AND uuid LIKE ?"
            q_params.append(filter_uuid_startswith + "%")

        cursor.execute(query, q_params)
        rows = cursor.fetchall()

        experiments_list = []
        for row in rows:
            experiments_list.append({
                'name': row[0],
                'uuid': row[1],
                'project': row[2],
                'status': row[3],
                'created_at': row[4],
                'expireAt': row[5]
            })

        return jsonify(experiments_list), 200

    except Exception as e:
        app.logger.error(f"Error listing experiments: {e}")
        return jsonify({'error': str(e)}), 500

# -------------------------------------------------------------------
# Background Task: Delete expired documents every minute
# -------------------------------------------------------------------
def delete_expired_documents():
    with app.app_context():
        now = datetime.now(timezone.utc)
        cursor.execute("SELECT name, expireAt FROM experiments")
        rows = cursor.fetchall()
        deleted_count = 0

        for row in rows:
            exp_name = row[0]
            expire_at_str = row[1]
            try:
                expire_dt = datetime.fromisoformat(expire_at_str)
            except ValueError:
                continue
            if expire_dt <= now:
                cursor.execute("DELETE FROM experiments WHERE name = ?", (exp_name,))
                deleted_count += 1

        if deleted_count > 0:
            connection.commit()
            app.logger.info(f"Deleted {deleted_count} expired record(s) from SQLite.")

def schedule_deletion():
    while True:
        delete_expired_documents()
        time.sleep(60)

# -------------------------------------------------------------------
# Initialize Management Node at Startup
# -------------------------------------------------------------------
def initialize_management_node():
    """
    At startup, run the terminal command:
      experimentStatus -j UCY-CS499-DC,management-node
    Parse the JSON output and store the management node information in the SQLite DB.
    """
    cmd = ["experimentStatus", "-j", "UCY-CS499-DC,management-node"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        app.logger.error("Failed to run experimentStatus command for management node")
        return

    try:
        response = json.loads(result.stdout)
        mgmt_uuid = response.get("uuid", "")
        expires_str = response.get("expires", "")
        if not mgmt_uuid or not expires_str:
            app.logger.error("Missing uuid or expires field in management node response")
            return

        # Parse the expires field (e.g., "2025-02-25T03:25:59Z")
        expire_at = datetime.strptime(expires_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)

        global management_node_info
        management_node_info = {
            'name': "management-node",
            'uuid': mgmt_uuid,
            'project': "UCY-CS499-DC",
            'status': response.get("status", "unknown"),
            'created_at': now.isoformat(),
            'expireAt': expire_at.isoformat()
        }
        
        cursor.execute("""
            INSERT OR REPLACE INTO experiments (name, uuid, project, status, created_at, expireAt)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            management_node_info['name'],
            management_node_info['uuid'],
            management_node_info['project'],
            management_node_info['status'],
            management_node_info['created_at'],
            management_node_info['expireAt']
        ))
        connection.commit()
        app.logger.info("Management node initialized and stored in DB using terminal command.")
    except Exception as e:
        app.logger.error(f"Error processing management node info: {e}")

# -------------------------------------------------------------------
# Background Task: Monitor and Extend Management Node
# -------------------------------------------------------------------
def monitor_management_node():
    """
    Background thread that checks if the management node's remaining time is less than one hour.
    If so, and if the last experiment's duration exceeds the remaining time, extend the management node.
    """
    while True:
        global management_node_info, last_experiment
        if management_node_info:
            expire_at = datetime.fromisoformat(management_node_info['expireAt'])
            now = datetime.now(timezone.utc)
            time_remaining = expire_at - now
            app.logger.info(f"Management node time remaining: {time_remaining}")
            if time_remaining < timedelta(hours=1):
                if last_experiment:
                    experiment_duration_hours = float(last_experiment.get('duration', 0)) / 3600.0
                    remaining_hours = time_remaining.total_seconds() / 3600.0
                    if experiment_duration_hours > remaining_hours:
                        extra_hours = experiment_duration_hours - remaining_hours
                        reason = (
                            "Extending management node because the last experiment's duration "
                            f"({experiment_duration_hours:.2f} hours) exceeds the remaining time "
                            f"({remaining_hours:.2f} hours). This extension is necessary to ensure "
                            "the continuity of ongoing experiments and to avoid any disruptions. "
                            "Please approve this extension request to maintain the stability and "
                            "reliability of the system."
                        )
                        app.logger.info(f"Extending management node by {extra_hours:.2f} hours with reason: {reason}")
                        extend_params = {
                            'proj': "UCY-CS499-DC",
                            'experiment': "management-node",
                            'extra_hours': extra_hours,
                            'reason': reason
                        }
                        config = {
                            "debug": 0,
                            "impotent": 0,
                            "verify": 0,
                            "certificate": GLOBAL_CERTIFICATE,
                        }
                        server = xmlrpc.EmulabXMLRPC(config)
                        (exitval, response) = api.extendExperiment(server, extend_params).apply()
                        if exitval == 0:
                            new_expire_at = expire_at + timedelta(hours=extra_hours)
                            management_node_info['expireAt'] = new_expire_at.isoformat()
                            cursor.execute("UPDATE experiments SET expireAt = ? WHERE name = ?",
                                (management_node_info['expireAt'], "management-node"))
                            connection.commit()
                            app.logger.info(
                                f"Management node extended successfully.\n"
                                f"Previous expiration time: {expire_at.isoformat()}\n"
                                f"New expiration time: {new_expire_at.isoformat()}\n"
                                f"Extended by: {extra_hours:.2f} hours\n"
                                f"Reason: {reason}"
                            )
                        else:
                            app.logger.error("Failed to extend management node.")
        time.sleep(300)  # Check every 5 minutes
# Start background deletion thread
threading.Thread(target=schedule_deletion, daemon=True).start()

# -------------------------------------------------------------------
# Main entry point
# -------------------------------------------------------------------
if __name__ == '__main__':
    result = subprocess.run(["python3", "./dns.py"], capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print("dns.py encountered an error")
    
    # Initialize management node information at startup
    initialize_management_node()
    
    # Start background thread to monitor and extend management node if needed
    threading.Thread(target=monitor_management_node, daemon=True).start()

    port = 8080
    app.run(debug=True, port=port, host='0.0.0.0')

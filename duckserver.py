import json
import re
import time
import requests
import threading
from io import BytesIO
from datetime import datetime, timedelta, timezone
import tempfile
import sqlite3

from flask import Flask, request, jsonify, Request
import CloudLabAPI.src.emulab_sslxmlrpc.client.api as api
import CloudLabAPI.src.emulab_sslxmlrpc.xmlrpc as xmlrpc

app = Flask(__name__)
app.logger.setLevel('INFO')

# -------------------------------------------------------------------
# DuckDNS Config
# -------------------------------------------------------------------
DOMAIN = 'terraform-cloudlab'  # your DuckDNS subdomain (no ".duckdns.org")
TOKEN = 'YOUR_DUCKDNS_TOKEN'
# If you trust DuckDNS auto-detection of your public IP:
# UPDATE_URL = f'https://www.duckdns.org/update?domains={DOMAIN}&token={TOKEN}&ip='
# Or, to force an IP (e.g. 155.98.36.7):
UPDATE_URL = f'https://www.duckdns.org/update?domains={DOMAIN}&token={TOKEN}&ip=155.98.36.7'

def duckdns_single_update():
    """
    Update DuckDNS once and exit.
    """
    try:
        response = requests.get(UPDATE_URL)
        app.logger.info(f"DuckDNS single update response: {response.text}")
    except Exception as e:
        app.logger.error(f"Error updating DuckDNS: {e}")

# -------------------------------------------------------------------
# SQLite Initialization
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
# Error Constants
# -------------------------------------------------------------------
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
# Helper Functions
# -------------------------------------------------------------------
def is_valid_json(json_str):
    try:
        json.loads(json_str)
        return True
    except json.JSONDecodeError:
        return False

def json_to_dict(json_string):
    return json.loads(json_string)

def dict_to_json(dictionary):
    return json.dumps(dictionary)

def parse_uuid_from_response(response_string: str) -> str:
    match = re.search(r"UUID:\s+([a-z0-9-]+)", response_string, re.IGNORECASE)
    if match:
        return match.group(1)
    return ""

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
            if is_valid_json(value):
                value_dict = json_to_dict(value)
                # If there's a nested JSON string for sharedVlans, parse that too
                if "sharedVlans" in value_dict and isinstance(value_dict["sharedVlans"], str):
                    value_dict["sharedVlans"] = json_to_dict(value_dict["sharedVlans"])
                params[key] = value_dict
            else:
                return (), ("Invalid bindings json", 400)

    return (temp_file_path, params), ("", 200)

# -------------------------------------------------------------------
# CloudLab Endpoints
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
    server = xmlrpc.EmulabXMLRPC(config)

    if 'bindings' in params and isinstance(params['bindings'], dict):
        params['bindings'] = dict_to_json(params['bindings'])

    max_retries = 5
    retry_delay = 3
    exitval, response = RESPONSE_ERROR, None
    for attempt in range(1, max_retries + 1):
        (exitval, response) = api.startExperiment(server, params).apply()
        app.logger.info(f"startExperiment attempt {attempt}/{max_retries}: exitval={exitval}, response={response}")
        if exitval == 0:
            break
        time.sleep(retry_delay)

    if exitval != 0:
        return ERRORMESSAGES.get(exitval, ERRORMESSAGES[RESPONSE_ERROR])

    cloudlab_uuid = parse_uuid_from_response(str(response))
    if not cloudlab_uuid:
        status_params = {
            'proj': params['proj'],
            'experiment': f"{params['proj']},{params['name']}"
        }
        (status_exitval, status_response) = api.experimentStatus(server, status_params).apply()
        if status_exitval == 0:
            cloudlab_uuid = parse_uuid_from_response(str(status_response))
        else:
            cloudlab_uuid = "unknown"

    if not cloudlab_uuid:
        cloudlab_uuid = "unknown"

    now = datetime.now(timezone.utc)
    expire_at = now + timedelta(hours=16)

    cursor.execute("""
        INSERT OR REPLACE INTO experiments (name, uuid, project, status, created_at, expireAt)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        params['name'],
        cloudlab_uuid,
        params['proj'],
        'started',
        now.isoformat(),
        expire_at.isoformat()
    ))
    connection.commit()

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
    server = xmlrpc.EmulabXMLRPC(config)

    max_retries = 5
    retry_delay = 2
    for attempt in range(1, max_retries + 1):
        (exitval, response) = api.experimentStatus(server, params).apply()
        if response is not None and hasattr(response, 'output'):
            return (str(response.output), ERRORMESSAGES[exitval][1])
        time.sleep(retry_delay)

    return ("No valid status after multiple retries", 500)

@app.route('/experiment', methods=['DELETE'])
def terminateExperiment():
    app.logger.info("terminateExperiment")
    args, err = parseArgs(request)
    errVal, errCode = err
    if errCode != 200:
        return err
    file, params = args

    config = {
        "debug": 0,
        "impotent": 0,
        "verify": 0,
        "certificate": file,
    }
    server = xmlrpc.EmulabXMLRPC(config)

    (exitval, response) = api.terminateExperiment(server, params).apply()
    if exitval == 0:
        uuid_to_delete = params.get('experiment') or params.get('name', '')
        cursor.execute("SELECT name FROM experiments WHERE uuid = ?", (uuid_to_delete,))
        rows = cursor.fetchall()

        if rows:
            for row in rows:
                exp_name = row[0]
                cursor.execute("DELETE FROM experiments WHERE name = ?", (exp_name,))
            connection.commit()

        return ERRORMESSAGES[exitval]
    else:
        return ERRORMESSAGES.get(exitval, ERRORMESSAGES[RESPONSE_ERROR])

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
        return jsonify({'error': str(e)}), 500

# -------------------------------------------------------------------
# Expired Document Deletion
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
# Main
# -------------------------------------------------------------------
if __name__ == '__main__':
    # 1. Single DuckDNS update
    duckdns_single_update()

    # 2. Start the thread for expired document cleanup
    threading.Thread(target=schedule_deletion, daemon=True).start()

    # 3. Start Flask
    port = 8080
    app.run(debug=True, port=port, host='0.0.0.0')


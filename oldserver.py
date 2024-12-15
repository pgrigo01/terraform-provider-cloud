import json
import time
from io import BytesIO

from flask import Flask, request, jsonify, Request
import CloudLabAPI.src.emulab_sslxmlrpc.client.api as api
import CloudLabAPI.src.emulab_sslxmlrpc.xmlrpc as xmlrpc
import tempfile

from db import get_db_connection, Vlan

app = Flask(__name__)
app.logger.setLevel('DEBUG')  # Set the logging level as needed

RESPONSE_SUCCESS = 0
RESPONSE_BADARGS = 1
RESPONSE_ERROR = 2
RESPONSE_FORBIDDEN = 3
RESPONSE_BADVERSION = 4
RESPONSE_SERVERERROR = 5
RESPONSE_TOOBIG = 6
RESPONSE_REFUSED = 7  # Emulab is down, try again later.
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


def is_valid_json(json_str):
    try:
        jsonString = json.loads(json_str)
        return jsonString
    except json.JSONDecodeError:
        return False


def json_to_dict(json_string):
    """
    Convert JSON string to dictionary.

    Args:
    json_string (str): JSON string to convert.

    Returns:
    dict: Dictionary converted from the JSON string.
    """
    return json.loads(json_string)


def dict_to_json(dictionary):
    """
    Convert dictionary to JSON string.

    Args:
    dictionary (dict): Dictionary to convert.

    Returns:
    str: JSON string converted from the dictionary.
    """
    return json.dumps(dictionary)


def parseArgs(request: Request):
    # parseFile
    if 'file' not in request.files:
        return (), ("No file provided", 400)
    file = request.files['file']

    # Check if a file was provided
    if file.filename == '':
        return (), ("No file selected", 400)

    # Read file content into BytesIO
    file_content = BytesIO()
    file.save(file_content)

    # Save file content to a temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False)
    temp_file.write(file_content.getvalue())
    temp_file_path = temp_file.name
    temp_file.close()

    params = {}
    for key, value in request.form.items():
        if key != 'bindings':
            params[key] = value.replace('"', '')
        else:
            if is_valid_json(value) != False:
                value_dict = json_to_dict(value)
                if "sharedVlans" in value_dict.keys():
                    value_dict["sharedVlans"] = json_to_dict(value_dict["sharedVlans"])
                params[key] = value_dict
            else:
                return (), ("Invalid bindings json", 400)
    return (temp_file_path, params), ("", 200)


@app.route('/experiment', methods=['POST'])
def startExperiment():
    app.logger.info("startExperiment")

    # Check if the 'file' key is in the request files
    app.logger.info('Parsing Arguments')
    args, err = parseArgs(request)
    errVal, errCode = err
    if errCode != 200:
        return err
    file, params = args
    if 'proj' not in list(params.keys()) or 'profile' not in list(params.keys()):
        return "Project and/or profile param not provided", 400

    config = {
        "debug": 0,
        "impotent": 0,
        "verify": 0,
        "certificate": file,
    }
    app.logger.info(f'Server configuration: {config}')
    server = xmlrpc.EmulabXMLRPC(config)

    createdVlans = []
    app.logger.info('Checking vlans')
    if 'sharedVlans' in params['bindings'].keys():
        sharedVlans = params['bindings']['sharedVlans']
        for vlan in sharedVlans:
            dbVlan = Vlan.filterByName(vlan['name'])
            if dbVlan is None:
                app.logger.info(f'Experiment {params["name"]} will create vlan {vlan["name"]}')
                vlan['createSharedVlan'] = "true"
                newDbVlan = Vlan(vlan['name'], params['name'], False)
                newDbVlan.save()
                createdVlans.append(newDbVlan)
            else:
                app.logger.info(f'Experiment {params["name"]} will use existing vlan {vlan["name"]}')
                while not dbVlan.ready:
                    app.logger.info(f'Experiment {params["name"]} waiting for {vlan["name"]} to be ready')
                    dbVlan = dbVlan.updateFromCloudlabAndDB(app, server, params['proj'])
                    if dbVlan is not None:
                        if dbVlan.ready:
                            vlan['connectSharedVlan'] = "true"
                            app.logger.info(f'Vlan {vlan["name"]} is ready')
                    else:
                        break
                    time.sleep(2)
                if dbVlan is None:
                    app.logger.info(f'Experiment {params["name"]} will create vlan {vlan["name"]}')
                    vlan['createSharedVlan'] = "true"
                    newDbVlan = Vlan(vlan['name'], params['name'], False)
                    newDbVlan.save()
                    createdVlans.append(newDbVlan)
    else:
        app.logger.info('No vlans')

    app.logger.info('Starting Experiment')
    params['bindings'] = dict_to_json(params['bindings'])
    app.logger.info(f'Experiment parameters: {params}')
    (exitval, response) = api.startExperiment(server, params).apply()
    app.logger.info(f'ExitVal: {exitval}')
    app.logger.info(f'Response: {response}')
    if exitval != 0:
        for vlan in createdVlans:
            vlan.delete()
    if exitval in ERRORMESSAGES.keys():
        return ERRORMESSAGES[exitval]
    return ERRORMESSAGES[RESPONSE_ERROR]


@app.route('/experiment', methods=['GET'])
def experimentStatus():
    app.logger.info("experimentStatus")

    # Check if the 'file' key is in the request files
    app.logger.info('Parsing Arguments')
    args, err = parseArgs(request)
    errVal, errCode = err
    if errCode != 200:
        return err
    file, params = args
    if 'proj' not in list(params.keys()) or 'experiment' not in list(params.keys()):
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

    dbVlan = Vlan.filterByExperiment(params['experiment'])
    if dbVlan is not None:
        dbVlan.updateFromCloudlabAndDB(app, server, params['proj'])
    app.logger.info(f'Experiment parameters: {params}')
    (exitval, response) = api.experimentStatus(server, params).apply()
    app.logger.info(f'ExitVal: {exitval}')
    app.logger.info(f'Response: {response}')
    return (response.output, ERRORMESSAGES[exitval][1])


@app.route('/experiment', methods=['DELETE'])
def terminateExperiment():
    app.logger.info("terminateExperiment")

    # Check if the 'file' key is in the request files
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
    app.logger.info(f'Server configuration: {config}')
    server = xmlrpc.EmulabXMLRPC(config)

    app.logger.info(f'Experiment parameters: {params}')
    (exitval, response) = api.terminateExperiment(server, params).apply()
    app.logger.info(f'ExitVal: {exitval}')
    app.logger.info(f'Response: {response}')
    return ERRORMESSAGES[exitval]


if __name__ == '__main__':
    # Specify the port you want to use, for example, port 8080
    port = 8080
    app.run(debug=True, port=port, host='0.0.0.0')

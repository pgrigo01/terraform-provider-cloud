from io import BytesIO

from flask import Flask, request, jsonify, Request
import CloudLabAPI.src.emulab_sslxmlrpc.client.api as api
import CloudLabAPI.src.emulab_sslxmlrpc.xmlrpc as xmlrpc
import tempfile

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
    RESPONSE_SEARCHFAILED: ('No such instance', 400),
    RESPONSE_ALREADYEXISTS: ('Already Exists', 400)
}


def parseArgs(request: Request):
    # parseFile
    if 'file' not in request.files:
        return (), ("No file provided", 400)
    file = request.files['file']
    # app.logger.info(file)

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
    paramKeys = list(request.form.keys())
    for key, value in request.form.items():
        params[key] = value.replace('"', '')
    return (temp_file_path, params), ("", 200)


@app.route('/startExperiment')
def startExperiment():
    app.logger.info("startExperiment")

    # Check if the 'file' key is in the request files
    app.logger.info('Parsing Arguments')
    args, err = parseArgs(request)
    errVal, errCode = err
    if errCode != 200:
        return err
    file, params = args
    if not 'proj' in list(params.keys()) or not 'profile' in list(params.keys()):
        return "Project and profile param not provided", 400
    app.logger.info(f'Arguments parsed: {file} {params}')

    config = {
        "debug": 0,
        "impotent": 0,
        "verify": 0,
        "certificate": file,
    }
    app.logger.info(f'Server configuration: {config}')
    server = xmlrpc.EmulabXMLRPC(config)

    app.logger.info('Starting Experiment')
    app.logger.info(f'Experiment parameters: {params}')
    (exitval, response) = api.startExperiment(server, params).apply()
    app.logger.info(f'ExitVal: {exitval}')
    app.logger.info(f'Response: {response}')
    return ERRORMESSAGES[exitval]


@app.route('/terminateExperiment')
def terminateExperiment():
    app.logger.info("terminateExperiment")

    # Check if the 'file' key is in the request files
    app.logger.info('Parsing Arguments')
    args, err = parseArgs(request)
    errVal, errCode = err
    if errCode != 200:
        return err
    file, params = args
    app.logger.info(f'Arguments parsed: {file} {params}')

    config = {
        "debug": 0,
        "impotent": 0,
        "verify": 0,
        "certificate": file,
    }
    app.logger.info(f'Server configuration: {config}')
    server = xmlrpc.EmulabXMLRPC(config)

    app.logger.info('Getting Experiment UUID')
    app.logger.info(f'Experiment parameters: {params}')
    (exitval, response) = api.experimentStatus(server, params).apply()
    app.logger.info(f'ExitVal: {exitval}')
    # Create a dictionary from the key-value pairs
    response_dict = {key: value for key, value in zip(response.output.split()[::2], response.output.split()[1::2])}
    experiment_uuid = response_dict["UUID:"]
    app.logger.info(f'Experiment UUID: {experiment_uuid}')
    (exitval, response) = api.terminateExperiment(server, {'experiment': experiment_uuid}).apply()
    return ERRORMESSAGES[exitval]


@app.route('/test', methods=['GET'])
def test():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    file = request.files['file']
    # app.logger.info(file)

    # Check if a file was provided
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    # Read file content into BytesIO
    file_content = BytesIO()
    file.save(file_content)

    # Save file content to a temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False)
    temp_file.write(file_content.getvalue())
    temp_file_path = temp_file.name
    temp_file.close()
    app.logger.info(temp_file_path)

    app.logger.info(params)
    return


@app.route('/upload', methods=['POST'])
def upload_file():
    config = {
        "debug": 0,
        "impotent": 0,
        "verify": 0,
        "uploaded_file": "path/to/file"
    }
    # Check if the 'file' key is in the request files
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files['file']
    app.logger.info(file)

    # Check if a file was provided
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    # Read file content into BytesIO
    file_content = BytesIO()
    file.save(file_content)

    # Save file content to a temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False)
    temp_file.write(file_content.getvalue())
    temp_file_path = temp_file.name
    temp_file.close()

    # Update config dictionary with the temporary file path
    config['uploaded_file_path'] = temp_file_path
    app.logger.info(temp_file_path)

    # Use temp_file_path with ctx.load_cert_chain
    # Example: ctx.load_cert_chain(temp_file_path)

    return jsonify({"message": "File received successfully"})


if __name__ == '__main__':
    # Specify the port you want to use, for example, port 8080
    port = 8080
    app.run(debug=True, port=port, host='0.0.0.0')

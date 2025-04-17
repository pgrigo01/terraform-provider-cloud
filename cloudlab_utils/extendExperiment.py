#!/usr/bin/env python3
import subprocess
import time
import sys

MAX_RETRIES = 5  # Maximum number of retries
RETRY_DELAY = 5  # Delay between retries in seconds

def extend_experiment(project_and_name: str, hours_to_extend: float, message: str = None):
    """
    Extends the specified experiment by the given number of hours.
    
    If an empty response is received from the extendExperiment command, 
    it is treated as a successful extension.
    
    :param project_and_name: A string in the format "Project,ExperimentName".
    :param hours_to_extend: Number of hours to extend (float or int; should be an integer value when sent).
    :param message: An optional message describing the reason for extension.
    """
    if message is None:
        message = ("I need extra time because I am developing an algorithm to keep "
                   "an elastic VLAN active and all participating nodes active.")

    # Build the command with the proper parameters.
    cmd = ["extendExperiment", "-m", message, project_and_name, str(hours_to_extend)]
    
    attempt = 0
    while attempt < MAX_RETRIES:
        try:
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode("utf-8").strip()
            # If output is empty, assume the extension was granted.
            if output:
                print("Extend Experiment Output:")
                print(output)
            else:
                print("Received empty response, extension was granted.")
                time.sleep(3)
            return  # Successful extension; exit function.
        except subprocess.CalledProcessError as e:
            error_message = e.output.decode("utf-8").strip()
            if "SSL: UNEXPECTED_EOF_WHILE_READING" in error_message:
                print(f"Attempt {attempt + 1}: SSL error encountered. Retrying in {RETRY_DELAY} seconds...")
            else:
                print("Error calling extendExperiment:")
                print(error_message)
                return  # For non-retryable errors, exit.
        attempt += 1
        time.sleep(RETRY_DELAY)
    print("Max retries reached. The experiment extension request may have failed.")

if __name__ == '__main__':
    extend_experiment("UCY-CS499-DC,extensionTesting", 1)
    # if len(sys.argv) > 2:
    #     project_and_name = sys.argv[1]
    #     hours = float(sys.argv[2])
    #     extend_experiment(project_and_name, hours)
    # else:
    #     print("No arguments provided. Using default UCY-CS499-DC,management-node and 12 hours to extend.")
    #     extend_experiment("UCY-CS499-DC,management-node", 12)

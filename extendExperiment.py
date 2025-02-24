#!/usr/bin/env python3
import subprocess

def extend_management_node():
    # Message explaining the reason for the extension.
    message = (
        "The reason I need this extra time for the experiment is that I am developing an algorithm on a central management node. "
        "This algorithm ensures that the central management node remains active for as long as the last experiment is running. "
        "For example, if the central management node is set to expire in one hour, I will check if there are any experiments that started after it. "
        "If so, the node's duration should be extended by adding the remaining time of the latest experiment on that VLAN "
        "(for example, if two hours are left on the last experiment, then I need to add two hours to the central management node). "
        "This extension is necessary to prevent the loss of the database that stores information about these experiments."
    )
    # Command to extend the experiment.
    cmd = ["extendExperiment", "-m", message, "UCY-CS499-DC,management-node"]
    try:
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        print("Extend Experiment Output:")
        print(output.decode("utf-8"))
    except subprocess.CalledProcessError as e:
        print("Error calling extendExperiment:")
        print(e.output.decode("utf-8"))

if __name__ == '__main__':
    extend_management_node()

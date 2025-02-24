#!/usr/bin/env python3
import subprocess
import json
import time

def get_management_node_status():
    # Command to get the management node status in JSON format.
    cmd = ["experimentStatus", "-j", "UCY-CS499-DC,management-node"]
    attempts = 3
    for attempt in range(1, attempts + 1):
        try:
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
            output_str = output.decode("utf-8")
            data = json.loads(output_str)
            expires = data.get("expires", "No expiration info found")
            print("Management Node Expiration:", expires)
            return
        except Exception as e:
            print(f"Attempt {attempt} failed: {e}")
            if attempt < attempts:
                time.sleep(3)
            else:
                print("All attempts failed. Exiting.")
                
if __name__ == '__main__':
    get_management_node_status()

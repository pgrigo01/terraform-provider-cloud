#!/usr/bin/env python3
"""
This script reads a CSV file (cloudlab_experiments.csv) containing experiment records and verifies each experiment's existence 
by calling the 'experimentStatus' command. It checks for valid status responses for each experiment using the 'Project' and 
'Name' columns to form the experiment specification (formatted as "<Project>,<Name>"). Experiments that are not found 
(i.e., return a null status) are removed from the CSV file. The script overwrites the original CSV file with the cleaned data.
Additionally, it creates a new CSV file (experiment_expire_times.csv) that stores the valid experiments' project, name, 
and expiration time (expireTime) in the format: project,name,expireTime.
"""

import csv
import subprocess
import json
import time
import sys

def get_experiment_status(exp_spec):
    cmd = ["experimentStatus", "-j", exp_spec]
    attempts = 3
    for attempt in range(1, attempts + 1):
        try:
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
            data = json.loads(output.decode("utf-8"))
            return data
        except Exception as e:
            print(f"Attempt {attempt} for {exp_spec} failed: {e}")
            if attempt < attempts:
                time.sleep(3)
    return None

def getCSVExperimentsExpireTimes():
    input_csv = "cloudlab_experiments.csv"
    # Overwrite original CSV with valid experiments.
    output_csv = "cloudlab_experiments.csv"
    # New file to store project,name,expireTime
    expire_csv = "experiment_expire_times.csv"

    updated_rows = []
    expire_rows = []
    removed_experiments = []

    try:
        with open(input_csv, newline="") as csvfile:
            reader = csv.DictReader(csvfile)
            headers = reader.fieldnames
            if not headers or 'Project' not in headers or 'Name' not in headers:
                print("Error: CSV does not contain the expected 'Project' and 'Name' columns.")
                sys.exit(1)

            for row in reader:
                exp_spec = f"{row['Project']},{row['Name']}"
                print(f"Processing experiment: {exp_spec}")
                status = get_experiment_status(exp_spec)
                if status:
                    print(f"{exp_spec} is valid.")
                    updated_rows.append(row)
                    expire_time = status.get("expires", "No expiration info found")
                    expire_rows.append({
                        "Project": row["Project"],
                        "Name": row["Name"],
                        "ExpireTime": expire_time
                    })
                else:
                    print(f"{exp_spec} not found. Removing from CSV.")
                    removed_experiments.append(exp_spec)
    except Exception as e:
        print(f"Error reading CSV: {e}")
        sys.exit(1)

    try:
        # Overwrite the original CSV with only valid experiments.
        with open(output_csv, "w", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=headers)
            writer.writeheader()
            for row in updated_rows:
                writer.writerow(row)
        print(f"CSV saved as {output_csv}.")
        if removed_experiments:
            print("Removed experiments:", removed_experiments)
    except Exception as e:
        print(f"Error writing to CSV: {e}")
        sys.exit(1)

    try:
        # Write out expiration times for valid experiments.
        expire_headers = ["Project", "Name", "ExpireTime"]
        with open(expire_csv, "w", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=expire_headers)
            writer.writeheader()
            for row in expire_rows:
                writer.writerow(row)
        print(f"Experiment expiration times saved to {expire_csv}.")
    except Exception as e:
        print(f"Error writing to {expire_csv}: {e}")
        sys.exit(1)

if __name__ == "__main__":
    getCSVExperimentsExpireTimes()

#!/usr/bin/env python3
import sys
import getpass
import csv
import math
from datetime import datetime, timezone

from cloudlab_utils import chromeExperimentCollector
from cloudlab_utils import firefoxExperimentCollector
from cloudlab_utils import getCSVExperimentInfo
from cloudlab_utils import extendExperiment

def parse_expire_time(expire_str):
    """
    Parse a timestamp string into a timezone-aware datetime in UTC.
    If the string is naive, assume UTC.
    """
    expire_time = None
    try:
        # Try parsing assuming the format without timezone info
        expire_time = datetime.strptime(expire_str, "%Y-%m-%d %H:%M:%S")
        # Assume naive timestamps are in UTC
        expire_time = expire_time.replace(tzinfo=timezone.utc)
    except ValueError:
        try:
            # Try ISO format parsing which may include timezone info
            expire_time = datetime.fromisoformat(expire_str)
            # If the parsed time is naive, assume UTC; otherwise, convert to UTC.
            if expire_time.tzinfo is None:
                expire_time = expire_time.replace(tzinfo=timezone.utc)
            else:
                expire_time = expire_time.astimezone(timezone.utc)
        except Exception as e:
            print(f"Error parsing expiration time '{expire_str}': {e}")
            return None
    return expire_time

def extendAllExperimentsToLast(username, password, hour_threshold=1.0):
    """
    1) Refresh experiment data (cloudlab_experiments.csv) via experimentCollector.
    2) Update expiration times (experiment_expire_times.csv) via getCSVExperimentInfo.
    3) Read experiment_expire_times.csv to find the latest expiration (all times converted to UTC).
    4) For each experiment that expires before the latest time, extend it IF the difference in hours is >= hour_threshold.
       We only round up if the raw difference >= hour_threshold, to avoid extending for small differences.
    """
    print("=== Step 1: Collecting experiment data ===")
    chromeExperimentCollector.getExperiments(username, password)
    # firefoxExperimentCollector.getExperiments(username, password)

    print("=== Step 2: Updating expiration times ===")
    getCSVExperimentInfo.getCSVExperimentsExpireTimes()

    print("=== Step 3: Reading experiment_expire_times.csv ===")
    experiments = []
    try:
        with open("experiment_expire_times.csv", newline="") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                project = row["Project"].strip()
                name = row["Name"].strip()
                expire_str = row["ExpireTime"].strip()
                if not expire_str:
                    continue

                expire_time = parse_expire_time(expire_str)
                if expire_time is None:
                    continue

                experiments.append((project, name, expire_time))
    except FileNotFoundError:
        print("experiment_expire_times.csv not found. Nothing to extend.")
        return

    if not experiments:
        print("No experiments found in experiment_expire_times.csv. Nothing to extend.")
        return

    # 4) Find the latest expiration time among all experiments (in UTC)
    latest_expire = max(exp[2] for exp in experiments)
    print(f"Latest expiration time found: {latest_expire}")

    # Current time in UTC
    now = datetime.now(timezone.utc)

    # Extend each experiment if it expires earlier than the latest time
    for (project, name, exp_time) in experiments:
        diff_seconds = (latest_expire - exp_time).total_seconds()
        if diff_seconds > 0:
            # Calculate the raw difference in hours
            float_hours = diff_seconds / 3600.0

            # If the difference is below the threshold, skip altogether
            if float_hours < hour_threshold:
                print(f"{project},{name} needs {float_hours:.2f} hours (< {hour_threshold} hour threshold). Skipping.")
                continue

            # Otherwise, we round up the hours
            rounded_hours = math.ceil(float_hours)

            message = f"Extending experiment {project},{name} to match the last experiment running expiration time."
            print(f"Extending {project},{name} by {rounded_hours} hours (rounded up from {float_hours:.2f} hours).")
            extendExperiment.extend_experiment(
                f"{project},{name}",
                rounded_hours,
                message=message
            )
        else:
            print(f"{project},{name} already extends to {exp_time}, no extension needed.")

def main():
    """
    Gathers credentials and calls the extension logic.
    Usage:
      python3 extendAllToLastTest.py [username] [password]
    If username/password are not provided, you will be prompted.
    """
    # Attempt to read username and password from sys.argv
    if len(sys.argv) >= 3:
        username = sys.argv[1]
        password = sys.argv[2]
    else:
        username = input("Enter CloudLab username: ").strip()
        password = getpass.getpass("Enter CloudLab password: ").strip()

    if not username or not password:
        print("Error: Username or password cannot be empty.")
        sys.exit(1)

    # Run the extension logic with a 1-hour threshold
    extendAllExperimentsToLast(username, password, hour_threshold=1.0)

if __name__ == "__main__":
    main()





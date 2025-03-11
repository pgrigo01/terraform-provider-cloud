import csv
import subprocess
import os
# Define the fields you want to keep
desired_fields = ['Name', 'Project']


with open('cloudlab_experiments.csv', newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        # Create a new dictionary with only the desired fields
        filtered_row = {field: row[field] for field in desired_fields}
        print(filtered_row)
        str = 'terminateExperiment ' + filtered_row['Project'] + ',' + filtered_row['Name']
        exit_status = os.system(str)
        print(exit_status)
        
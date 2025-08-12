import csv
import json
import os

# Create output directory
output_dir = 'oaa_files'
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Load data
with open('identities.csv', 'r') as f:
    identities = list(csv.DictReader(f))

with open('resources.csv', 'r') as f:
    resources = list(csv.DictReader(f))

with open('permissions.csv', 'r') as f:
    permissions = list(csv.DictReader(f))

with open('entitlements.csv', 'r') as f:
    entitlements = list(csv.DictReader(f))

# Create application.json
app_data = {
    "application_name": "Dunder Mifflin HRIS",
    "application_type": "HRIS",
    "description": "Employee management for Dunder Mifflin Paper Company"
}

with open(os.path.join(output_dir, 'application.json'), 'w') as f:
    json.dump(app_data, f, indent=2)

# Copy CSV files to output directory
for filename in ['identities.csv', 'resources.csv', 'permissions.csv', 'entitlements.csv']:
    with open(filename, 'r') as infile, open(os.path.join(output_dir, filename), 'w') as outfile:
        outfile.write(infile.read())

print("OAA files generated successfully in 'oaa_files' directory")

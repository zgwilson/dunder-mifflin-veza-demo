#!/usr/bin/env python3
"""Uses the CustomIdPProvider class to create an OAA Custom IdP from CSV imports.

Reads users, groups, and group memberships from CSV files and maps them to the IdP.

To run the code, you will need to export environment variables for the Veza URL and API key.

Example:
export VEZA_API_KEY="your_api_key_here"
export VEZA_URL="https://your-veza-host"
./dmi_idp_csv.py

Copyright 2022 Veza Technologies Inc.

Use of this source code is governed by the MIT
license that can be found in the LICENSE file or at
https://opensource.org/licenses/MIT.
"""

import csv
import os
import sys
import importlib.metadata
from oaaclient.client import OAAClient, OAAClientError
from oaaclient.templates import CustomIdPProvider, OAAPropertyType

def read_csv_file(file_path):
    """Read a CSV file and return a list of dictionaries."""
    try:
        with open(file_path, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            return [row for row in reader]
    except FileNotFoundError:
        print(f"Error: CSV file {file_path} not found", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading CSV file {file_path}: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    # Check oaaclient version
    try:
        oaaclient_version = importlib.metadata.version("oaaclient")
        print(f"Debug: Using oaaclient version {oaaclient_version}")
    except importlib.metadata.PackageNotFoundError:
        print("Warning: Could not determine oaaclient version", file=sys.stderr)

    # Load environment variables
    veza_api_key = os.getenv('VEZA_API_KEY')
    veza_url = os.getenv('VEZA_URL')
    if None in (veza_url, veza_api_key):
        print("Unable to locate all environment variables", file=sys.stderr)
        sys.exit(1)

    # Initialize OAA client
    veza_con = OAAClient(url=veza_url, api_key=veza_api_key)

    # Create CustomIdPProvider instance
    custom_idp = CustomIdPProvider(name="DMI_IDP", idp_type="CustomIdP", domain="veza.com")

    # Define custom properties for User
    try:
        custom_idp.property_definitions.define_user_property("full_name", OAAPropertyType.STRING)
        custom_idp.property_definitions.define_user_property("job_title", OAAPropertyType.STRING)
        custom_idp.property_definitions.define_user_property("department", OAAPropertyType.STRING)
        print("Defined custom properties: full_name, job_title, department")
    except Exception as e:
        print(f"Warning: Failed to define properties via define_user_property: {e}", file=sys.stderr)
        print("Falling back to setting properties directly")

    # Define paths to CSV files
    csv_dir = "csv_data"
    users_file = os.path.join(csv_dir, "idp_users.csv")
    groups_file = os.path.join(csv_dir, "idp_groups.csv")
    group_memberships_file = os.path.join(csv_dir, "idp_group_memberships.csv")

    # Read and process users
    users_data = read_csv_file(users_file)
    for user in users_data:
        name = user.get('full_name', user['identity'])
        custom_idp.add_user(name=name)
        if user['identity']:
            # Set identity directly via identities list
            try:
                custom_idp.users[name].identities = [user['identity']]
                print(f"Debug: Added identity {user['identity']} to user {name}")
            except AttributeError as e:
                print(f"Error: Failed to set identities for {name}: {e}", file=sys.stderr)
                print(f"Debug: CustomIdPUser attributes for {name}: {dir(custom_idp.users[name])}", file=sys.stderr)
                sys.exit(1)
        # Set custom attributes
        custom_attrs = {attr: user[attr] for attr in ['full_name', 'job_title', 'department'] if user.get(attr)}
        if custom_attrs:
            try:
                for key, value in custom_attrs.items():
                    custom_idp.users[name].set_property(key, value)
                print(f"Set properties for user {name} via set_property: {custom_attrs}")
            except Exception as e:
                print(f"Warning: Failed to set properties via set_property for {name}: {e}", file=sys.stderr)
                # Fallback to direct properties dictionary
                try:
                    for key, value in custom_attrs.items():
                        custom_idp.users[name].properties[key] = value
                    print(f"Set properties for user {name} via properties dict: {custom_attrs}")
                except Exception as e2:
                    print(f"Warning: Failed to set properties via properties dict for {name}: {e2}", file=sys.stderr)
                    print(f"Debug: IdP User attributes for {name}: {dir(custom_idp.users[name])}", file=sys.stderr)
        if user.get('is_active'):
            custom_idp.users[name].is_active = user['is_active'].lower() == 'true'

    # Read and process groups
    groups_data = read_csv_file(groups_file)
    for group in groups_data:
        group_name = group['name']
        custom_idp.add_group(name=group_name)
        # Debug: Inspect group ID
        group_obj = custom_idp.groups[group_name]
        group_dict = group_obj.to_dict()
        group_id = getattr(group_obj, 'id', group_dict.get('id', group_dict.get('name', 'Not found')))
        print(f"Debug: IdP Group {group_name} ID: {group_id}")
        print(f"Debug: IdP Group {group_name} to_dict: {group_dict}")

    # Read and process group memberships
    group_memberships_data = read_csv_file(group_memberships_file)
    for membership in group_memberships_data:
        user_identity = membership['user_identity']
        group_name = membership['group_name']
        # Map user_identity to full_name
        user = next((u for u in users_data if u['identity'] == user_identity), None)
        if not user or user['full_name'] not in custom_idp.users:
            print(f"Error: User {user_identity} not found for group membership", file=sys.stderr)
            continue
        if group_name not in custom_idp.groups:
            print(f"Error: Group {group_name} not found for group membership", file=sys.stderr)
            continue
        custom_idp.users[user['full_name']].add_groups([group_name])
        print(f"Debug: Added {user['full_name']} to group {group_name}")

    # Debug print (corrected)
    print(f"Debug: CustomIdPProvider payload: {custom_idp.get_payload()}")

    # Push the metadata payload to Veza
    provider_name = "DMI_IDP"
    provider = veza_con.get_provider(provider_name)
    if provider:
        print(f"-- Found existing provider: {provider['name']} ({provider['id']})")
    else:
        print(f"++ Creating Provider {provider_name}")
        provider = veza_con.create_provider(provider_name, "identity_provider")

    try:
        response = veza_con.push_application(
            provider_name=provider_name,
            data_source_name=f"{custom_idp.name} ({custom_idp.idp_type})",
            application_object=custom_idp,
            save_json=False
        )
        if response.get("warnings", None):
            print("-- Push succeeded with warnings:")
            for e in response["warnings"]:
                print(f"  - {e}")
    except OAAClientError as e:
        print(f"-- Error: {e.error}: {e.message} ({e.status_code})", file=sys.stderr)
        if hasattr(e, "details"):
            for d in e.details:
                print(f"  -- {d}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""Uses the CustomApplication class to create an OAA Custom application from CSV imports.

Reads users, groups, resources, permissions, and identity-to-permissions mappings from CSV files
and maps them to the application and resources.

To run the code, you will need to export environment variables for the Veza URL and API key.

Example:
export VEZA_API_KEY="your_api_key_here"
export VEZA_URL="https://your-veza-host"
./dmi_app_csv.py

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
from oaaclient.templates import CustomApplication, OAAPermission, OAAPropertyType

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

    # Create CustomApplication instance
    custom_app = CustomApplication(name="DMIAPP", application_type="Custom")

    # Define custom properties for LocalUser
    try:
        custom_app.property_definitions.define_local_user_property("full_name", OAAPropertyType.STRING)
        custom_app.property_definitions.define_local_user_property("job_title", OAAPropertyType.STRING)
        custom_app.property_definitions.define_local_user_property("branch", OAAPropertyType.STRING)
        print("Defined custom properties: full_name, job_title, branch")
    except Exception as e:
        print(f"Warning: Failed to define properties via define_local_user_property: {e}", file=sys.stderr)
        print("Falling back to setting properties directly")

    # Define paths to CSV files
    csv_dir = "csv_data"
    users_file = os.path.join(csv_dir, "users.csv")
    groups_file = os.path.join(csv_dir, "groups.csv")
    resources_file = os.path.join(csv_dir, "resources.csv")
    permissions_file = os.path.join(csv_dir, "permissions.csv")
    identity_to_permissions_file = os.path.join(csv_dir, "identity_to_permissions.csv")

    # Read and process permissions
    permissions_data = read_csv_file(permissions_file)
    for perm in permissions_data:
        perm_name = perm['name']
        perm_types = [getattr(OAAPermission, p.strip()) for p in perm['permissions'].split(';')]
        custom_app.add_custom_permission(perm_name, perm_types)

    # Read and process resources
    resources_data = read_csv_file(resources_file)
    resource_map = {}
    for res in resources_data:
        name = res['name']
        resource_type = res['resource_type']
        parent_name = res['parent_name'] if res['parent_name'] else None
        description = res['description'] if res['description'] else None

        if parent_name:
            parent_resource = resource_map.get(parent_name)
            if not parent_resource:
                print(f"Error: Parent resource {parent_name} not found for {name}", file=sys.stderr)
                sys.exit(1)
            resource = parent_resource.add_sub_resource(name=name, resource_type=resource_type, description=description)
        else:
            resource = custom_app.add_resource(name=name, resource_type=resource_type, description=description)
        resource_map[name] = resource

    # Read and process users
    users_data = read_csv_file(users_file)
    for user in users_data:
        name = user.get('full_name', user['name'])
        custom_app.add_local_user(name=name)
        if user['identity']:
            # Option 1: Use email as identity
            custom_app.local_users[name].add_identity(user['identity'])
            # Option 2: Use full_name as identity (uncomment to test)
            # custom_app.local_users[name].add_identity(name)
            print(f"Debug: Added identity {user['identity']} to user {name}")
        # Set custom attributes
        custom_attrs = {attr: user[attr] for attr in ['full_name', 'job_title', 'branch'] if user.get(attr)}
        if custom_attrs:
            try:
                for key, value in custom_attrs.items():
                    custom_app.local_users[name].set_property(key, value)
                print(f"Set properties for user {name} via set_property: {custom_attrs}")
            except Exception as e:
                print(f"Warning: Failed to set properties via set_property for {name}: {e}", file=sys.stderr)
                # Fallback to direct properties dictionary
                try:
                    for key, value in custom_attrs.items():
                        custom_app.local_users[name].properties[key] = value
                    print(f"Set properties for user {name} via properties dict: {custom_attrs}")
                except Exception as e2:
                    print(f"Warning: Failed to set properties via properties dict for {name}: {e2}", file=sys.stderr)
                    print(f"Debug: LocalUser attributes for {name}: {dir(custom_app.local_users[name])}", file=sys.stderr)
        if user.get('is_active'):
            custom_app.local_users[name].is_active = user['is_active'].lower() == 'true'

    # Read and process groups
    groups_data = read_csv_file(groups_file)
    for group in groups_data:
        group_name = group['name']
        custom_app.add_local_group(name=group_name)
        # Debug: Inspect group ID
        group_obj = custom_app.local_groups[group_name]
        group_dict = group_obj.to_dict()
        group_id = getattr(group_obj, 'id', group_dict.get('id', group_dict.get('name', 'Not found')))
        print(f"Debug: LocalGroup {group_name} ID: {group_id}")
        print(f"Debug: LocalGroup {group_name} to_dict: {group_dict}")

    # Assign users to groups
    for user in users_data:
        if user.get('groups'):
            for group_name in user['groups'].split(';'):
                if group_name in custom_app.local_groups:
                    custom_app.local_users[user['full_name']].add_group(group_name)
                    print(f"Debug: Assigned user {user['full_name']} to group {group_name}")

    # Read and process identity-to-permissions mappings
    identity_to_permissions_data = read_csv_file(identity_to_permissions_file)
    for mapping in identity_to_permissions_data:
        identity = mapping['identity']
        identity_type = mapping['identity_type']
        permission = mapping['permission']
        resource_name = mapping['resource_name'] if mapping['resource_name'] else None

        if identity_type == 'local_user':
            # Map identity to full_name
            user = next((u for u in users_data if u['name'] == identity), None)
            if not user or user['full_name'] not in custom_app.local_users:
                print(f"Error: User {identity} not found", file=sys.stderr)
                continue
            entity = custom_app.local_users[user['full_name']]
            print(f"Debug: Mapped identity {identity} to user {user['full_name']}")
        elif identity_type == 'local_group':
            if identity not in custom_app.local_groups:
                print(f"Error: Group {identity} not found", file=sys.stderr)
                continue
            entity = custom_app.local_groups[identity]
        else:
            print(f"Error: Invalid identity_type {identity_type} for {identity}", file=sys.stderr)
            continue

        if resource_name:
            resource = resource_map.get(resource_name)
            if not resource:
                print(f"Error: Resource {resource_name} not found for {identity}", file=sys.stderr)
                continue
            entity.add_permission(permission=permission, resources=[resource])
        else:
            entity.add_permission(permission=permission, apply_to_application=True)

    # Debug: Inspect full payload
    print(f"Debug: CustomApplication payload: {custom_app.app_dict()}")

    # Push the metadata payload to Veza
    provider_name = "DMI_APP"
    provider = veza_con.get_provider(provider_name)
    if provider:
        print(f"-- Found existing provider: {provider['name']} ({provider['id']})")
    else:
        print(f"++ Creating Provider {provider_name}")
        provider = veza_con.create_provider(provider_name, "application")

    try:
        response = veza_con.push_application(
            provider_name=provider_name,
            data_source_name=f"{custom_app.name} ({custom_app.application_type})",
            application_object=custom_app,
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
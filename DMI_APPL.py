#!/usr/bin/env python3
"""Uses the `CustomApplication` class to create an OAA Custom application.

Creates local users, groups assignments, and maps permissions to the application
and resources.

To run the code, you will need to export environment variables for the Veza URL,
user and API keys.

Example:
    ```
    export VEZA_API_KEY="your_api_key_here"
    export VEZA_URL="https://your-veza-host"
    ./dmi_app.py
    ```

Copyright 2022 Veza Technologies Inc.

Use of this source code is governed by the MIT
license that can be found in the LICENSE file or at
https://opensource.org/licenses/MIT.

"""

from oaaclient.client import OAAClient, OAAClientError
from oaaclient.templates import CustomApplication, OAAPermission
import os
import sys

def main():

    # OAA requires an API token, which you can generate from your Veza user profile
    # Export the API token, and Veza URL as environment variables
    # Making them available to your connector in this way keeps credentials out of the source code
    veza_api_key = os.getenv('VEZA_API_KEY')
    veza_url = os.getenv('VEZA_URL')
    if None in (veza_url, veza_api_key):
        print("Unable to locate all environment variables")
        sys.exit(1)

    # Instantiates a client connection. The client will confirm the credentials and Veza URL are valid
    # Checking this early helps prevents connection failures in the final stage
    veza_con = OAAClient(url=veza_url, api_key=veza_api_key)

    # Create an instance of the OAA CustomApplication class, modeling the application name and type
    # `name` will be displayed in the Veza UI
    # `application_type` should be a short key reflecting the source application authorization is being modeled for
    # You can use the same type for multiple applications
    custom_app = CustomApplication(name="DMIAPP", application_type="Custom")

    # In the OAA payload, each permission native to the custom app is mapped to the Veza effective permission (data/non-data C/R/U/D).
    # Permissions must be defined before they can be referenced, as they are discovered or ahead of time.
    # For each custom application permission, bind them to the Veza permissions using the `OAAPermission` enum:
    custom_app.add_custom_permission("ViewDept", [OAAPermission.DataRead])
    custom_app.add_custom_permission("EditDept", [OAAPermission.DataRead, OAAPermission.DataWrite])
    custom_app.add_custom_permission("ApproveTime", [OAAPermission.DataRead, OAAPermission.DataWrite])
    custom_app.add_custom_permission("AccessBranch", [OAAPermission.DataRead])
    custom_app.add_custom_permission("OrderPaper", [OAAPermission.DataRead])
    custom_app.add_custom_permission("ManagePricing", [OAAPermission.DataRead, OAAPermission.DataWrite])
    custom_app.add_custom_permission("ManageWarehouse", [OAAPermission.DataRead, OAAPermission.DataWrite])

    # Create resources and sub-resources to model the entities in the application
    # To Veza, an application can be a single entity or can contain resources and sub-resources
    # Utilizing resources enables tracking of authorizations to specific components of the system being modeled
    # Setting a `resource_type` can help group entities of the same type for reporting/queries
    scranton_branch = custom_app.add_resource(name="Scranton Branch", resource_type="branch", description="Scranton Branch")
    #management_dept = custom_app.add_resource(name="Management", resource_type="department", description="Management Department", parent=scranton_branch)
    management_dept = scranton_branch.add_sub_resource(name="Management",resource_type="child", description="Management Department")
    #warehouse_dept = custom_app.add_resource(name="Warehouse", resource_type="department", description="Warehouse Department", parent=scranton_branch)
    warehouse_dept = scranton_branch.add_sub_resource(name="Warehouse",resource_type="child", description="Warehouse Department")
    #sales_dept = custom_app.add_resource(name="Sales", resource_type="department", description="Sales Department", parent=scranton_branch)
    sales_dept = scranton_branch.add_sub_resource(name="Sales",resource_type="child", description="Sales Department")
    bond_paper = custom_app.add_resource(name="Bond Paper", resource_type="paper_type", description="Bond Paper")
    letterhead_paper = custom_app.add_resource(name="Company Letterhead", resource_type="paper_type", description="Company Letterhead")

    # Define local users
    custom_app.add_local_user("michael")
    custom_app.local_users["michael"].add_identity("zwilson+Michael.Scott@veza.com")
    #michael = custom_app.add_local_user("michael", identities="zwilson+Michael.Scott@veza.com")
    #jim = custom_app.add_local_user("jim", identities="jim@dm.com", custom_attributes={"job_title": "Salesman", "branch": "Scranton"})
    custom_app.add_local_user("jim")
    #custom_app.local_users["jim"].add_identity("zwilson+Jim.Halpert@veza.com")
    #pam = custom_app.add_local_user("pam", identities="pam@dm.com", custom_attributes={"job_title": "Receptionist", "branch": "Scranton"})
    custom_app.add_local_user("pam")
    #custom_app.local_users["pam"].add_identity("zwilson+pam@veza.com")
    #dwight = custom_app.add_local_user("dwight", identities="dwight@dm.com", custom_attributes={"job_title": "Salesman", "branch": "Scranton"})
    custom_app.add_local_user("dwight")
    #custom_app.local_users["dwight"].add_identity("zwilson+Dwight.Schrute@veza.com")

    # Define local groups
    custom_app.add_local_group("managers")
    custom_app.add_local_group("sales")

    # Assign users to groups
    custom_app.local_users["michael"].add_group("managers")
    custom_app.local_users["jim"].add_group("sales")
    custom_app.local_users["dwight"].add_group("sales")

    # Assign permissions to users and groups
    custom_app.local_users["michael"].add_permission(permission="ViewDept", resources=[management_dept])
    custom_app.local_users["michael"].add_permission(permission="EditDept", resources=[management_dept])
    custom_app.local_users["michael"].add_permission(permission="ApproveTime", resources=[management_dept])
    custom_app.local_users["michael"].add_permission(permission="AccessBranch", resources=[scranton_branch])
    custom_app.local_users["michael"].add_permission(permission="OrderPaper", resources=[bond_paper, letterhead_paper])
    custom_app.local_users["michael"].add_permission(permission="ManagePricing", resources=[scranton_branch])
    custom_app.local_users["michael"].add_permission(permission="ManageWarehouse", resources=[warehouse_dept])

    custom_app.local_users["jim"].add_permission(permission="ViewDept", resources=[sales_dept])
    custom_app.local_users["jim"].add_permission(permission="AccessBranch", resources=[scranton_branch])
    custom_app.local_users["jim"].add_permission(permission="OrderPaper", resources=[bond_paper, letterhead_paper])

    custom_app.local_users["pam"].add_permission(permission="ViewDept", resources=[management_dept])
    custom_app.local_users["pam"].add_permission(permission="AccessBranch", resources=[scranton_branch])

    custom_app.local_users["dwight"].add_permission(permission="ViewDept", resources=[sales_dept])
    custom_app.local_users["dwight"].add_permission(permission="AccessBranch", resources=[scranton_branch])
    custom_app.local_users["dwight"].add_permission(permission="ManageWarehouse", resources=[warehouse_dept])

    # Once all authorizations have been mapped, the final step is to publish the app to Veza
    # Connect to the API to Push to Veza, define the provider and create if necessary:

    provider_name = "DMI_APP"
    provider = veza_con.get_provider(provider_name)
    if provider:
        print("-- Found existing provider")
    else:
        print(f"++ Creating Provider {provider_name}")
        provider = veza_con.create_provider(provider_name, "application")
    print(f"-- Provider: {provider['name']} ({provider['id']})")

    # Push the metadata payload:

    try:
        response = veza_con.push_application(provider_name,
                                               data_source_name=f"{custom_app.name} ({custom_app.application_type})",
                                               application_object=custom_app,
                                               save_json=False
                                               )
        if response.get("warnings", None):
            # Veza may return warnings on a successful uploads. These are informational warnings that did not stop the processing
            # of the OAA data but may be important. Specifically identities that cannot be resolved will be returned here.
            print("-- Push succeeded with warnings:")
            for e in response["warnings"]:
                print(f"  - {e}")
    except OAAClientError as e:
        # If there are any errors connecting to the Veza API or processing the payload the client will raise an `OAAClientError`
        print(f"-- Error: {e.error}: {e.message} ({e.status_code})", file=sys.stderr)
        if hasattr(e, "details"):
            # Error details will have specifics on any issues encountered processing the payload
            for d in e.details:
                print(f"  -- {d}", file=sys.stderr)
    return

if __name__ == '__main__':
    main()

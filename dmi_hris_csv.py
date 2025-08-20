#!/usr/bin/env python3
import csv
import json
import logging
from oaaclient.client import OAAClient, OAAClientError
from oaaclient.templates import HRISProvider, OAAPropertyType

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

def main():
    # Initialize HRIS provider
    hris = HRISProvider(
        name="DMI_HRIS",
        hris_type="custom",
        description="Dunder Mifflin HRIS"
    )
    log.info(f"Debug: Using oaaclient version {OAAClient.__version__}")

    # Define custom properties
    hris.property_definitions.define_employee_property("full_name", OAAPropertyType.STRING)
    hris.property_definitions.define_employee_property("job_title", OAAPropertyType.STRING)
    hris.property_definitions.define_employee_property("department", OAAPropertyType.STRING)
    hris.property_definitions.define_employee_property("location", OAAPropertyType.STRING)
    hris.property_definitions.define_employee_property("start_date", OAAPropertyType.TIMESTAMP)
    hris.property_definitions.define_employee_property("status", OAAPropertyType.STRING)
    hris.property_definitions.define_employee_property("shift", OAAPropertyType.STRING)
    hris.property_definitions.define_employee_property("remote", OAAPropertyType.BOOLEAN)
    hris.property_definitions.define_employee_property("loa", OAAPropertyType.BOOLEAN)
    log.info("Defined custom properties: full_name, job_title, department, location, start_date, status, shift, remote, loa")

    # Read CSV
    csv_path = "csv/01984444-5546-72a7-9f40-5fce598136ea_01984444-5606-740d-8bb5-f598fb6025f3.csv"
    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Add employee
            employee = hris.add_employee(
                name=f"{row['FirstName']} {row['LastName']}",
                identity=row['Email'],
                employee_id=row['employee_number'],
                is_active=row['Status'] == "Active"
            )
            log.info(f"Debug: Added identity {row['Email']} to employee {row['name']}")

            # Set custom properties
            employee.set_property("full_name", f"{row['FirstName']} {row['LastName']}")
            employee.set_property("job_title", row['JobTitle'])
            employee.set_property("department", row['Department'])
            employee.set_property("location", row['Location'])
            employee.set_property("start_date", row['StartDate'])
            employee.set_property("status", row['Status'])
            employee.set_property("shift", row['Shift'])
            employee.set_property("remote", row['Remote'].lower() == "yes")
            employee.set_property("loa", row['LOA'].lower() == "yes")
            log.info(f"Set properties for employee {row['name']}: {employee.custom_properties}")

            # Set manager (if valid)
            if row['ManagerID']:
                try:
                    employee.set_manager(row['ManagerID'])
                    log.info(f"Debug: Set manager {row['ManagerID']} for employee {row['name']}")
                except Exception as e:
                    log.warning(f"Failed to set manager {row['ManagerID']} for {row['name']}: {e}")

            # Add to department as group (optional)
            if row['Department']:
                group = hris.add_group(name=row['Department'])
                employee.add_groups([row['Department']])
                log.info(f"Debug: Added {row['name']} to group {row['Department']}")

    # Generate and print payload
    payload = hris.get_payload()
    log.info(f"Debug: HRISProvider payload: {json.dumps(payload, indent=2)}")

    # Push to Veza
    try:
        client = OAAClient(url=os.getenv("VEZA_URL"), token=os.getenv("VEZA_API_KEY"))
        client.push_hris_metadata(
            provider_name="DMI_HRIS",
            hris_type="custom",
            metadata=payload
        )
        log.info("HRIS data push succeeded")
    except OAAClientError as e:
        log.error(f"Error pushing HRIS data: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
#!/bin/bash

# Create directory structure
mkdir -p dmi_csv hris_csv

# Create HRIS CSV files
cat > hris_csv/departments.csv << 'EOF'
department_id,department_name,parent_id
D001,Executive,
D002,Sales,D001
D003,Manufacturing,D001
EOF

cat > hris_csv/locations.csv << 'EOF'
location_id,location_name
LAX,Los Angeles
SCR,Scranton PA
EOF

cat > hris_csv/employees.csv << 'EOF'
employee_id,employee_name,identity,hire_date,title
E1001,Michael Scott,zwilson+Michael.Scott@veza.com,1999-04-01,Branch Manager
E1002,Jim Halpert,zwilson+Jim.Halpert@veza.com,2001-06-15,Salesman
E1003,Pam Beesly,zwilson+pam@veza.com,2001-08-12,Receptionist
E1004,Dwight Schrute,zwilson+Dwight.Schrute@veza.com,2000-08-01,Salesman
EOF

cat > hris_csv/employee_department.csv << 'EOF'
employee_id,department_id
E1001,D001
E1002,D002
E1003,D002
E1004,D002
EOF

cat > hris_csv/employee_location.csv << 'EOF'
employee_id,location_id
E1001,SCR
E1002,SCR
E1003,SCR
E1004,SCR
EOF

# Create Custom App CSV files
cat > dmi_csv/application.csv << 'EOF'
application_id,name,application_type
DMIAPP,DMIAPP,Custom
EOF

cat > dmi_csv/permissions.csv << 'EOF'
permission_id,permission_name,veza_permissions
ViewDept,ViewDept,DataRead
EditDept,EditDept,"DataRead,DataWrite"
ApproveTime,ApproveTime,"DataRead,DataWrite"
AccessBranch,AccessBranch,DataRead
OrderPaper,OrderPaper,DataRead
ManagePricing,ManagePricing,"DataRead,DataWrite"
ManageWarehouse,ManageWarehouse,"DataRead,DataWrite"
EOF

cat > dmi_csv/resources.csv << 'EOF'
resource_id,name,resource_type,description,parent_id
ScrantonBranch,Scranton Branch,branch,Scranton Branch,
ManagementDept,Management,department,Management Department,ScrantonBranch
WarehouseDept,Warehouse,department,Warehouse Department,ScrantonBranch
SalesDept,Sales,department,Sales Department,ScrantonBranch
BondPaper,Bond Paper,paper_type,Bond Paper,
LetterheadPaper,Company Letterhead,paper_type,Company Letterhead,
EOF

cat > dmi_csv/users.csv << 'EOF'
user_id,username,identity
michael,michael,zwilson+Michael.Scott@veza.com
jim,jim,zwilson+Jim.Halpert@veza.com
pam,pam,zwilson+pam@veza.com
dwight,dwight,zwilson+Dwight.Schrute@veza.com
EOF

cat > dmi_csv/groups.csv << 'EOF'
group_id,group_name
managers,managers
sales,sales
EOF

cat > dmi_csv/user_group_membership.csv << 'EOF'
user_id,group_id
michael,managers
jim,sales
dwight,sales
EOF

cat > dmi_csv/entitlements.csv << 'EOF'
principal_id,permission_id,resource_id
user:michael,ViewDept,ManagementDept
user:michael,EditDept,ManagementDept
user:michael,ApproveTime,ManagementDept
user:michael,AccessBranch,ScrantonBranch
user:michael,OrderPaper,BondPaper
user:michael,OrderPaper,LetterheadPaper
user:michael,ManagePricing,ScrantonBranch
user:michael,ManageWarehouse,WarehouseDept
user:jim,ViewDept,SalesDept
user:jim,AccessBranch,ScrantonBranch
user:jim,OrderPaper,BondPaper
user:jim,OrderPaper,LetterheadPaper
user:dwight,ViewDept,SalesDept
user:dwight,AccessBranch,ScrantonBranch
user:dwight,ManageWarehouse,WarehouseDept
user:pam,ViewDept,ManagementDept
user:pam,AccessBranch,ScrantonBranch
EOF

# Clone the OAA community repo
echo "Cloning OAA community repo..."
git clone https://github.com/Veza/oaa-community.git

# Install dependencies
echo "Installing dependencies..."
cd oaa-community/quickstarts/hris_csv
pip install -r requirements.txt
cd ../app-csv-import
pip install -r requirements.txt
cd ../../..

# Create run scripts
cat > run_hris_import.sh << 'EOF'
#!/bin/bash
if [ -z "$VEZA_URL" ] || [ -z "$VEZA_API_KEY" ]; then
    echo "Error: Please set VEZA_URL and VEZA_API_KEY environment variables"
    exit 1
fi

echo "Running HRIS import..."
python oaa-community/quickstarts/hris_csv/import_hris_csv.py \
  --provider-name "HRIS" \
  --csv-dir "$(pwd)/hris_csv"
EOF

cat > run_app_import.sh << 'EOF'
#!/bin/bash
if [ -z "$VEZA_URL" ] || [ -z "$VEZA_API_KEY" ]; then
    echo "Error: Please set VEZA_URL and VEZA_API_KEY environment variables"
    exit 1
fi

echo "Running Custom App import..."
python oaa-community/quickstarts/app-csv-import/import_csv.py \
  --provider-name "DMI_APP" \
  --application-name "DMIAPP" \
  --csv-dir "$(pwd)/dmi_csv"
EOF

cat > run_all_imports.sh << 'EOF'
#!/bin/bash
if [ -z "$VEZA_URL" ] || [ -z "$VEZA_API_KEY" ]; then
    echo "Error: Please set VEZA_URL and VEZA_API_KEY environment variables"
    exit 1
fi

echo "Running HRIS import..."
./run_hris_import.sh

echo "Running Custom App import..."
./run_app_import.sh

echo "All imports complete!"
EOF

# Make scripts executable
chmod +x run_hris_import.sh run_app_import.sh run_all_imports.sh

echo "Setup complete! Directory structure created:"
echo ""
tree -L 2 2>/dev/null || find . -maxdepth 2 -type d | sort
echo ""
echo "CSV files created in:"
echo "  - hris_csv/ (HRIS data)"
echo "  - dmi_csv/ (Custom app data)"
echo ""
echo "To run the imports:"
echo "  1. Set your environment variables:"
echo "     export VEZA_URL='https://your-veza-host'"
echo "     export VEZA_API_KEY='your_api_key_here'"
echo ""
echo "  2. Run individual imports:"
echo "     ./run_hris_import.sh    # Import HRIS data"
echo "     ./run_app_import.sh     # Import Custom App data"
echo ""
echo "  3. Or run both at once:"
echo "     ./run_all_imports.sh"

#!/bin/bash
if [ -z "$VEZA_URL" ] || [ -z "$VEZA_API_KEY" ]; then
    echo "Error: Please set VEZA_URL and VEZA_API_KEY environment variables"
    exit 1
fi

python oaa-community/quickstarts/app-csv-import/app_csv_import.py \
  --provider-name "DMI_APP" \
  --application-name "DMIAPP" \
  --csv-dir "$(pwd)/dmi_csv"

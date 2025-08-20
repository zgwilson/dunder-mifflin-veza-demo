#!/bin/bash
if [ -z "$VEZA_URL" ] || [ -z "$VEZA_API_KEY" ]; then
    echo "Error: Please set VEZA_URL and VEZA_API_KEY environment variables"
    exit 1
fi

echo "Running HRIS import..."
python oaa-community/quickstarts/hris_csv/hris_import_csv.py \
  --provider-name "HRIS" \
  --application-name "HRIS_APP" \
  --csv-dir "$(pwd)/hris_csv"

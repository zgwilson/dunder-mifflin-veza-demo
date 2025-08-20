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

#!/bin/bash
# Upload new environmental data for processing

if [ $# -eq 0 ]; then
    echo "Usage: $0 <csv_file>"
    echo "Example: $0 new_environmental_data.csv"
    exit 1
fi

CSV_FILE="$1"
DATE_FOLDER=$(date +%Y-%m-%d)
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
FILENAME="environmental_data_${TIMESTAMP}.csv"

echo "Uploading $CSV_FILE to Azure Storage..."

az storage blob upload \
  --account-name stenvpipelinenm5piaoe \
  --container-name environmental-data \
  --name "landing/${DATE_FOLDER}/${FILENAME}" \
  --file "$CSV_FILE" \
  --overwrite

echo "✓ File uploaded to: landing/${DATE_FOLDER}/${FILENAME}"
echo "Pipeline will automatically process this file."
#!/bin/bash

# Script to properly destroy Azure resources
# This ensures storage accounts are emptied before destruction

set -e

echo "Starting Azure resource cleanup..."

# Get storage account name from Terraform state
STORAGE_ACCOUNT=$(terraform output -raw storage_account_name 2>/dev/null || echo "")

if [ ! -z "$STORAGE_ACCOUNT" ]; then
    echo "Emptying storage account: $STORAGE_ACCOUNT"
    
    # Delete all blobs in all containers
    az storage blob delete-batch \
        --account-name "$STORAGE_ACCOUNT" \
        --source '$root' \
        --auth-mode login 2>/dev/null || true
    
    # Delete all containers
    az storage container list \
        --account-name "$STORAGE_ACCOUNT" \
        --auth-mode login \
        --query "[].name" -o tsv 2>/dev/null | \
    while read container; do
        if [ ! -z "$container" ]; then
            echo "Deleting container: $container"
            az storage container delete \
                --account-name "$STORAGE_ACCOUNT" \
                --name "$container" \
                --auth-mode login 2>/dev/null || true
        fi
    done
fi

echo "Running terraform destroy..."
terraform destroy -auto-approve

echo "Cleanup complete!"
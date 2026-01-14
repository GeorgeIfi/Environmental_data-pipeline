#!/bin/bash
# Synapse Cost Management Script

set -e

# Load terraform outputs
cd infra/terraform
SYNAPSE_WORKSPACE=$(terraform output -raw synapse_workspace_name)
RESOURCE_GROUP=$(terraform output -raw resource_group_name)

case "$1" in
    "pause")
        echo "Pausing Synapse workspace: $SYNAPSE_WORKSPACE"
        az synapse workspace pause \
          --name $SYNAPSE_WORKSPACE \
          --resource-group $RESOURCE_GROUP
        echo "✓ Synapse workspace paused - costs reduced by ~80%"
        ;;
    "resume")
        echo "Resuming Synapse workspace: $SYNAPSE_WORKSPACE"
        az synapse workspace resume \
          --name $SYNAPSE_WORKSPACE \
          --resource-group $RESOURCE_GROUP
        echo "✓ Synapse workspace resumed - ready for queries"
        ;;
    "status")
        echo "Checking Synapse workspace status..."
        az synapse workspace show \
          --name $SYNAPSE_WORKSPACE \
          --resource-group $RESOURCE_GROUP \
          --query "provisioningState" -o tsv
        ;;
    *)
        echo "Usage: $0 {pause|resume|status}"
        echo "  pause  - Pause workspace to save costs"
        echo "  resume - Resume workspace for use"
        echo "  status - Check current status"
        exit 1
        ;;
esac
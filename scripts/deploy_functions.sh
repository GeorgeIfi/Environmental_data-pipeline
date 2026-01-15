#!/bin/bash
# Deploy Azure Functions to Function App

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== Azure Functions Deployment ===${NC}"

# Load environment
if [ ! -f .env ]; then
    echo -e "${RED}❌ .env file not found${NC}"
    exit 1
fi

source .env

# Check if terraform outputs exist
if [ ! -f infra/terraform/outputs.json ]; then
    echo -e "${YELLOW}ℹ️ Running terraform to get outputs...${NC}"
    cd infra/terraform
    terraform output -json > outputs.json
    cd ../..
fi

# Extract function app name and endpoint
FUNCTION_APP_NAME=$(jq -r '.function_app_name.value // empty' infra/terraform/outputs.json || echo "")
FUNCTION_ENDPOINT=$(jq -r '.function_app_endpoint.value // empty' infra/terraform/outputs.json || echo "")

if [ -z "$FUNCTION_APP_NAME" ]; then
    echo -e "${RED}❌ Function App name not found in terraform outputs${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Function App: $FUNCTION_APP_NAME${NC}"
echo -e "${GREEN}✓ Endpoint: $FUNCTION_ENDPOINT${NC}"

# Install Azure Functions Core Tools if not present
if ! command -v func &> /dev/null; then
    echo -e "${YELLOW}Installing Azure Functions Core Tools...${NC}"
    npm install -g azure-functions-core-tools@4 --unsafe-perm=true --allow-root
fi

# Navigate to functions directory
cd azure_functions

# Install dependencies
echo -e "${YELLOW}Installing Python dependencies...${NC}"
pip install -r requirements.txt

# Publish to Azure Function App
echo -e "${YELLOW}Publishing functions to Azure...${NC}"
func azure functionapp publish "$FUNCTION_APP_NAME" --build remote

echo -e "${GREEN}✓ Functions deployed successfully!${NC}"
echo -e "${GREEN}✓ Function endpoints:${NC}"
echo -e "${GREEN}  - Bronze Ingest: ${FUNCTION_ENDPOINT}/api/bronze-ingest${NC}"
echo -e "${GREEN}  - Silver Transform: ${FUNCTION_ENDPOINT}/api/silver-transform${NC}"
echo -e "${GREEN}  - Gold Transform: ${FUNCTION_ENDPOINT}/api/gold-transform${NC}"

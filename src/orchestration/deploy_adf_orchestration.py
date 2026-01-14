#!/usr/bin/env python3
"""
Deploy ADF Pipeline and Trigger for Environmental Data Pipeline
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_prerequisites():
    """Check if all required environment variables are set"""
    required_vars = [
        "AZURE_TENANT_ID",
        "AZURE_CLIENT_ID", 
        "AZURE_CLIENT_SECRET",
        "AZURE_SUBSCRIPTION_ID",
        "AZURE_RESOURCE_GROUP",
        "AZURE_DATA_FACTORY_NAME"
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"ERROR: Missing required environment variables: {', '.join(missing_vars)}")
        sys.exit(1)
    
    print("✓ All required environment variables are set")

def deploy_pipeline():
    """Deploy the ADF pipeline"""
    print("Deploying ADF Pipeline...")
    
    # Import and run pipeline creation
    sys.path.append(str(Path(__file__).parent / "src" / "orchestration"))
    from create_adf_pipeline import create_pipeline
    
    try:
        create_pipeline()
        print("✓ Pipeline deployed successfully")
    except Exception as e:
        print(f"✗ Pipeline deployment failed: {e}")
        return False
    
    return True

def deploy_trigger():
    """Deploy and start the ADF trigger"""
    print("Deploying ADF Trigger...")
    
    # Import and run trigger creation
    sys.path.append(str(Path(__file__).parent / "src" / "orchestration"))
    from create_adf_trigger import create_schedule_trigger
    
    try:
        create_schedule_trigger()
        print("✓ Trigger deployed and started successfully")
    except Exception as e:
        print(f"✗ Trigger deployment failed: {e}")
        return False
    
    return True

def main():
    print("=== ADF Pipeline Deployment ===")
    
    # Check prerequisites
    check_prerequisites()
    
    # Deploy pipeline
    if not deploy_pipeline():
        sys.exit(1)
    
    # Deploy trigger
    if not deploy_trigger():
        sys.exit(1)
    
    print("\n🎉 ADF orchestration deployed successfully!")
    print("Your pipeline will now run automatically daily at 6 AM UTC")
    print(f"Monitor at: https://portal.azure.com -> Data Factory -> {os.getenv('AZURE_DATA_FACTORY_NAME')}")

if __name__ == "__main__":
    main()
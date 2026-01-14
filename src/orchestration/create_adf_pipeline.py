#!/usr/bin/env python3
import os
from azure.identity import ClientSecretCredential
from azure.mgmt.datafactory import DataFactoryManagementClient
from azure.mgmt.datafactory.models import (
    PipelineResource,
    CustomActivity,
    LinkedServiceReference,
)

def create_pipeline():
    # Get credentials from environment
    tenant_id = os.getenv("AZURE_TENANT_ID")
    client_id = os.getenv("AZURE_CLIENT_ID")
    client_secret = os.getenv("AZURE_CLIENT_SECRET")
    subscription_id = os.getenv("AZURE_SUBSCRIPTION_ID")
    resource_group = os.getenv("AZURE_RESOURCE_GROUP")
    data_factory_name = os.getenv("AZURE_DATA_FACTORY_NAME")

    if not all([tenant_id, client_id, client_secret, subscription_id, resource_group, data_factory_name]):
        raise RuntimeError("Missing one or more required AZURE_* environment variables")

    # Authenticate
    credential = ClientSecretCredential(
        tenant_id=tenant_id,
        client_id=client_id,
        client_secret=client_secret,
    )
    adf_client = DataFactoryManagementClient(credential, subscription_id)

    # Simple wait activity to demonstrate pipeline execution
    wait_activity = {
        "name": "WaitActivity",
        "type": "Wait",
        "description": "Simple wait activity for pipeline demonstration",
        "typeProperties": {
            "waitTimeInSeconds": 10
        }
    }

    pipeline = PipelineResource(
        activities=[wait_activity],
        description="Environmental Data Pipeline - Simple Wait Activity",
    )

    adf_client.pipelines.create_or_update(
        resource_group_name=resource_group,
        factory_name=data_factory_name,
        pipeline_name="EnvironmentalDataPipeline",
        pipeline=pipeline,
    )

    print("ADF Pipeline created successfully!")

if __name__ == "__main__":
    create_pipeline()

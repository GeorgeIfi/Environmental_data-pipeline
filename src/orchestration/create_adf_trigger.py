#!/usr/bin/env python3
import os
from datetime import datetime, timezone

from azure.identity import ClientSecretCredential
from azure.mgmt.datafactory import DataFactoryManagementClient
from azure.mgmt.datafactory.models import (
    ScheduleTrigger,
    ScheduleTriggerRecurrence,
    TriggerPipelineReference,
    PipelineReference,
    TriggerResource,
)

def create_schedule_trigger():
    # Get credentials from environment
    tenant_id = os.getenv("AZURE_TENANT_ID")
    client_id = os.getenv("AZURE_CLIENT_ID")
    client_secret = os.getenv("AZURE_CLIENT_SECRET")
    subscription_id = os.getenv("AZURE_SUBSCRIPTION_ID")
    resource_group = os.getenv("AZURE_RESOURCE_GROUP")
    data_factory_name = os.getenv("AZURE_DATA_FACTORY_NAME")
    
    # Authenticate
    credential = ClientSecretCredential(
        tenant_id=tenant_id,
        client_id=client_id,
        client_secret=client_secret,
    )
    adf_client = DataFactoryManagementClient(credential, subscription_id)
    
    # Reference the existing pipeline
    pipeline_ref = PipelineReference(
        type="PipelineReference",
        reference_name="EnvironmentalDataPipeline",
    )

    # Recurrence: daily at 06:00 UTC
    recurrence = ScheduleTriggerRecurrence(
        frequency="Day",
        interval=1,
        start_time=datetime(2024, 1, 1, 6, 0, 0, tzinfo=timezone.utc),
        time_zone="UTC",
    )

    # ScheduleTrigger properties
    schedule_trigger = ScheduleTrigger(
        description="Daily trigger for environmental data pipeline",
        recurrence=recurrence,
        pipelines=[
            TriggerPipelineReference(
                pipeline_reference=pipeline_ref
            )
        ],
    )

    # Wrap in TriggerResource (this is what ADF expects)
    trigger_resource = TriggerResource(
        properties=schedule_trigger
    )
    
    trigger_name = "DailyEnvironmentalDataTrigger"

    # Deploy trigger
    adf_client.triggers.create_or_update(
        resource_group_name=resource_group,
        factory_name=data_factory_name,
        trigger_name=trigger_name,
        trigger=trigger_resource,
    )
    
    # Start the trigger (use begin_start in this SDK)
    poller = adf_client.triggers.begin_start(
        resource_group_name=resource_group,
        factory_name=data_factory_name,
        trigger_name=trigger_name,
    )
    poller.result()  # wait for completion
    
    print("ADF Trigger created and started successfully!")

if __name__ == "__main__":
    create_schedule_trigger()

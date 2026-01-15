"""
Azure Data Factory: Alerts, Monitoring, and Failure-Handling Patterns

This guide demonstrates production-ready error handling for the orchestration_pipeline,
including retry policies, on-failure notifications, and alerting strategies.
"""

# ============================================================================
# 1. RETRY POLICIES
# ============================================================================

"""
Retry policies handle transient failures automatically.
Configure at the Activity level in your ADF pipeline.
"""

# JSON Definition for WebActivity with Retry
RETRY_POLICY_EXAMPLE = {
    "name": "BronzeIngestActivity",
    "type": "WebActivity",
    "typeProperties": {
        "method": "POST",
        "url": "https://{func_app}.azurewebsites.net/api/bronze-ingest",
        "headers": {
            "Content-Type": "application/json"
        },
        "body": {
            "storage_account": "stenvpipeline...",
            "container": "environmental-data",
            "csv_file": "landing/weather_raw.csv"
        },
        "authentication": {
            "type": "Anonymous"
        }
    },
    # Retry Configuration (auto-retry on transient failures)
    "policy": {
        "timeout": "7.00:00:00",          # 7 hours max execution
        "retry": 3,                        # Retry 3 times
        "retryIntervalInSeconds": 30,      # 30 seconds between retries
        "secureInput": False,
        "secureOutput": False
    }
}

# Exponential Backoff Pattern (manual implementation via multiple retries)
EXPONENTIAL_BACKOFF = {
    "policy": {
        "retry": 4,  # Total attempts: 1 initial + 4 retries
        "retryIntervalInSeconds": 10  # ADF doubles this internally (10, 20, 40, 80)
    }
}

# ============================================================================
# 2. ON-FAILURE ACTIVITIES (Send Email Alert)
# ============================================================================

"""
On-Failure activities trigger when a preceding activity fails.
Use these to send notifications, call webhooks, or log errors.
"""

# Pipeline JSON with On-Failure Activity
ON_FAILURE_EMAIL_PATTERN = {
    "activities": [
        {
            "name": "BronzeIngestActivity",
            "type": "WebActivity",
            "typeProperties": {
                "method": "POST",
                "url": "https://{func_app}.azurewebsites.net/api/bronze-ingest",
                "body": {}
            },
            "onFailure": [
                {
                    "dependencyConditions": ["Failed"],
                    "activities": [
                        {
                            "name": "SendFailureEmail",
                            "type": "WebActivity",
                            "typeProperties": {
                                "method": "POST",
                                "url": "https://prod-123.logic.azure.com:443/workflows/.../triggers/manual/invoke?api-version=2016-06-01&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=...",
                                "headers": {
                                    "Content-Type": "application/json"
                                },
                                "body": {
                                    "subject": "ADF Pipeline Failed: Bronze Ingestion",
                                    "body": "Pipeline @{pipeline().RunId} failed at @{utcNow()}\nError: @{activity('BronzeIngestActivity').Error.Message}",
                                    "to": "data-team@company.com"
                                },
                                "authentication": {
                                    "type": "Anonymous"
                                }
                            }
                        }
                    ]
                }
            ]
        }
    ]
}

# ============================================================================
# 3. ON-SUCCESS ACTIVITIES (Trigger Next Pipeline)
# ============================================================================

"""
On-Success activities create conditional flows.
Use these to chain dependent pipeline runs or log successful executions.
"""

CHAINED_PIPELINE_PATTERN = {
    "activities": [
        {
            "name": "GoldTransformActivity",
            "type": "WebActivity",
            "typeProperties": {
                "method": "POST",
                "url": "https://{func_app}.azurewebsites.net/api/gold-transform",
                "body": {}
            },
            "onSuccess": [
                {
                    "dependencyConditions": ["Succeeded"],
                    "activities": [
                        {
                            "name": "TriggerReportingPipeline",
                            "type": "ExecutePipeline",
                            "typeProperties": {
                                "pipeline": {
                                    "referenceName": "reporting-pipeline",
                                    "type": "PipelineReference"
                                },
                                "waitOnCompletion": True,
                                "parameters": {
                                    "date": "@pipeline().parameters.ProcessDate",
                                    "data_path": "gold/weather"
                                }
                            }
                        }
                    ]
                }
            ]
        }
    ]
}

# ============================================================================
# 4. ACTIVITY SKIP CONDITIONS
# ============================================================================

"""
Skip activities based on conditions (avoid failures entirely).
Useful for optional processing steps.
"""

CONDITIONAL_SKIP_PATTERN = {
    "name": "OptionalSilverTransform",
    "type": "WebActivity",
    "skipActivityOnFailure": False,  # Don't skip on failure, let it fail normally
    "typeProperties": {
        "method": "POST",
        "url": "https://{func_app}.azurewebsites.net/api/silver-transform",
        "body": {}
    },
    "dependsOn": [
        {
            "activity": "BronzeIngestActivity",
            "dependencyConditions": ["Succeeded"]  # Only run if Bronze succeeded
        }
    ]
}

# ============================================================================
# 5. TIMEOUT CONFIGURATION
# ============================================================================

"""
Set appropriate timeouts to prevent infinite hangs.
"""

TIMEOUT_PATTERNS = {
    # Short timeout for fast operations (Functions)
    "fast_operation": {
        "timeout": "0.00:05:00",  # 5 minutes
        "retry": 2,
        "retryIntervalInSeconds": 10
    },
    
    # Medium timeout for data processing
    "medium_operation": {
        "timeout": "0.01:00:00",  # 1 hour
        "retry": 1,
        "retryIntervalInSeconds": 30
    },
    
    # Long timeout for aggregation
    "long_operation": {
        "timeout": "1.00:00:00",  # 24 hours
        "retry": 0,
        "retryIntervalInSeconds": 0
    }
}

# ============================================================================
# 6. PIPELINE FAILURE TRIGGER
# ============================================================================

"""
Set up a trigger to notify when the entire pipeline fails.
Create an Action Group first, then create an Alert Rule.
"""

PIPELINE_FAILURE_TRIGGER = {
    "type": "Microsoft.Insights/actionGroups",
    "apiVersion": "2019-06-01",
    "name": "adf-failure-notification",
    "location": "global",
    "properties": {
        "enabled": True,
        "groupShortName": "ADF-FAIL",
        "emailReceivers": [
            {
                "name": "DataTeamEmail",
                "emailAddress": "data-team@company.com",
                "useCommonAlertSchema": True
            }
        ],
        "webhookReceivers": [
            {
                "name": "SlackNotification",
                "serviceUri": "https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
                "useCommonAlertSchema": True
            }
        ]
    }
}

# ============================================================================
# 7. MONITORING & ALERTS
# ============================================================================

"""
Use Azure Monitor to create alerts on pipeline failures.
"""

METRIC_ALERT_CONFIG = {
    "name": "ADF-PipelineFailureAlert",
    "type": "Microsoft.Insights/metricAlerts",
    "apiVersion": "2018-03-01",
    "location": "global",
    "properties": {
        "enabled": True,
        "scopes": [
            "/subscriptions/{subscription}/resourceGroups/rg-envpipeline-dev/providers/Microsoft.DataFactory/factories/adf-environmental-xxxxx"
        ],
        "criteria": {
            "odata.type": "Microsoft.Azure.Monitor.MultipleResourceMultipleMetricCriteria",
            "allOf": [
                {
                    "name": "PipelineFailureRate",
                    "metricName": "PipelineFailedRuns",
                    "dimensions": [
                        {
                            "name": "PipelineName",
                            "operator": "Include",
                            "values": ["orchestration_pipeline"]
                        }
                    ],
                    "operator": "GreaterThan",
                    "threshold": 0,
                    "timeAggregation": "Total"
                }
            ]
        },
        "windowSize": "PT5M",  # Check every 5 minutes
        "evaluationFrequency": "PT1M",  # Evaluate every 1 minute
        "actions": [
            {
                "actionGroupId": "/subscriptions/{subscription}/resourceGroups/rg-envpipeline-dev/providers/Microsoft.Insights/actionGroups/adf-failure-notification"
            }
        ]
    }
}

# ============================================================================
# 8. CUSTOM ERROR LOGGING
# ============================================================================

"""
Log detailed error information to Application Insights.
"""

ERROR_LOGGING_ACTIVITY = {
    "name": "LogFailureToAppInsights",
    "type": "WebActivity",
    "typeProperties": {
        "method": "POST",
        "url": "https://dc.applicationinsights.io/v2/track",
        "headers": {
            "Content-Type": "application/json"
        },
        "body": {
            "name": "Microsoft.ApplicationInsights.Event",
            "time": "@utcNow()",
            "iKey": "@{activity('GetAppInsightsKey').output}",
            "data": {
                "baseType": "EventData",
                "baseData": {
                    "ver": 2,
                    "name": "PipelineFailure",
                    "properties": {
                        "PipelineName": "@{pipeline().PipelineName}",
                        "RunId": "@{pipeline().RunId}",
                        "FailedActivity": "@{activity('FailedActivityName').ActivityName}",
                        "ErrorMessage": "@{activity('FailedActivityName').Error.Message}",
                        "ErrorCode": "@{activity('FailedActivityName').Error.ErrorCode}"
                    }
                }
            }
        },
        "authentication": {
            "type": "Anonymous"
        }
    }
}

# ============================================================================
# 9. DELTA/INCREMENTAL PROCESSING (Prevent Reprocessing)
# ============================================================================

"""
Avoid reprocessing failed data by tracking processed dates.
"""

DELTA_PROCESSING_PATTERN = {
    "activities": [
        {
            "name": "GetLastProcessedDate",
            "type": "Lookup",
            "typeProperties": {
                "source": {
                    "type": "AzureTableStorageSource",
                    "query": "SELECT PartitionKey, RowKey, ProcessedDate WHERE PipelineName eq 'orchestration_pipeline'"
                },
                "dataset": {
                    "referenceName": "ProcessingStateTable",
                    "type": "DatasetReference"
                },
                "firstRowOnly": True
            }
        },
        {
            "name": "BronzeIngestActivity",
            "type": "WebActivity",
            "typeProperties": {
                "method": "POST",
                "url": "https://{func_app}.azurewebsites.net/api/bronze-ingest",
                "body": {
                    "from_date": "@{activity('GetLastProcessedDate').output.firstRow.ProcessedDate}",
                    "to_date": "@{utcNow()}"
                }
            }
        },
        {
            "name": "UpdateProcessedDate",
            "type": "Copy",
            "typeProperties": {
                "source": {},
                "sink": {
                    "type": "AzureTableStorageSink",
                    "writeBatchSize": 1
                }
            },
            "dependsOn": [
                {
                    "activity": "BronzeIngestActivity",
                    "dependencyConditions": ["Succeeded"]
                }
            ]
        }
    ]
}

# ============================================================================
# 10. CIRCUIT BREAKER PATTERN
# ============================================================================

"""
Stop pipeline execution if too many consecutive failures occur.
Prevents cascading errors and saves costs.
"""

CIRCUIT_BREAKER_PATTERN = {
    "name": "CheckFailureCount",
    "type": "Lookup",
    "typeProperties": {
        "source": {
            "type": "AzureSqlSource",
            "sqlReaderQuery": """
            SELECT COUNT(*) as FailureCount 
            FROM dbo.PipelineRuns 
            WHERE PipelineName = 'orchestration_pipeline' 
            AND Status = 'Failed' 
            AND CreatedDate >= DATEADD(hour, -1, GETDATE())
            """
        },
        "dataset": {
            "referenceName": "MonitoringDatabase",
            "type": "DatasetReference"
        }
    }
}

CIRCUIT_BREAKER_DECISION = {
    "name": "ShouldProceed",
    "type": "IfCondition",
    "typeProperties": {
        "expression": "@less(int(activity('CheckFailureCount').output.firstRow.FailureCount), 5)",
        "ifFalseActivities": [
            {
                "name": "SendCircuitBreakerAlert",
                "type": "WebActivity",
                "typeProperties": {
                    "method": "POST",
                    "url": "https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
                    "body": {
                        "text": "🚨 CIRCUIT BREAKER TRIGGERED: 5+ failures in last hour. Pipeline halted."
                    }
                }
            }
        ],
        "ifTrueActivities": [
            {
                "name": "BronzeIngestActivity",
                "type": "WebActivity",
                "typeProperties": {}
            }
        ]
    }
}

# ============================================================================
# 11. DEAD LETTER QUEUE PATTERN
# ============================================================================

"""
Send failed messages to a dead letter queue for manual inspection/replay.
"""

DEAD_LETTER_PATTERN = {
    "name": "SendToDeadLetter",
    "type": "Copy",
    "typeProperties": {
        "source": {
            "type": "AzureBlobStorageSource",
            "wildcardFileName": "@{activity('BronzeIngestActivity').output.csv_file}"
        },
        "sink": {
            "type": "AzureBlobStorageSink"
        }
    },
    "inputs": [
        {
            "referenceName": "LandingBlobDataset",
            "type": "DatasetReference",
            "parameters": {
                "container": "environmental-data",
                "folder": "landing"
            }
        }
    ],
    "outputs": [
        {
            "referenceName": "DeadLetterBlobDataset",
            "type": "DatasetReference",
            "parameters": {
                "container": "environmental-data",
                "folder": "dead-letter/@{formatDateTime(utcNow(), 'yyyy-MM-dd')}"
            }
        }
    ]
}

# ============================================================================
# 12. SLACK INTEGRATION EXAMPLE
# ============================================================================

"""
Send real-time notifications to Slack on pipeline events.
"""

SLACK_SUCCESS_NOTIFICATION = {
    "name": "NotifySlackSuccess",
    "type": "WebActivity",
    "typeProperties": {
        "method": "POST",
        "url": "https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
        "body": {
            "text": "✅ Data Pipeline Succeeded",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"""*Pipeline:* orchestration_pipeline
*Status:* ✅ Success
*Duration:* @{{activity('GoldTransformActivity').output.executionDuration}}s
*Timestamp:* @{{utcNow()}}
*Run ID:* @{{pipeline().RunId}}"""
                    }
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "View in Portal"
                            },
                            "url": "https://portal.azure.com/#blade/HubsExtension/BrowseResourceBlade/resourceType/Microsoft.DataFactory%2Ffactories"
                        }
                    ]
                }
            ]
        }
    }
}

SLACK_FAILURE_NOTIFICATION = {
    "name": "NotifySlackFailure",
    "type": "WebActivity",
    "typeProperties": {
        "method": "POST",
        "url": "https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
        "body": {
            "text": "🚨 Data Pipeline Failed",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"""*Pipeline:* orchestration_pipeline
*Status:* ❌ Failed
*Failed Activity:* @{{activity('BronzeIngestActivity').ActivityName}}
*Error:* @{{activity('BronzeIngestActivity').Error.Message}}
*Timestamp:* @{{utcNow()}}"""
                    }
                }
            ]
        }
    }
}

# ============================================================================
# RECOMMENDATIONS
# ============================================================================

RECOMMENDATIONS = """
✅ PRODUCTION-READY FAILURE HANDLING CHECKLIST:

1. RETRY POLICIES
   ☐ Set retry count: 2-3 times for transient failures
   ☐ Set retry interval: 10-30 seconds
   ☐ Set timeout: Appropriate for each activity (5m - 1h)

2. ON-FAILURE NOTIFICATIONS
   ☐ Email alert to data team
   ☐ Slack notification to #data-alerts
   ☐ Send to monitoring database

3. MONITORING
   ☐ Create Action Group for notifications
   ☐ Set up metric alerts (FailedRuns > 0)
   ☐ Dashboard to view pipeline success rate
   ☐ Log errors to Application Insights

4. DATA PROTECTION
   ☐ Implement delta/incremental processing
   ☐ Track last processed date
   ☐ Use dead letter queue for failures
   ☐ Archive failed inputs for replay

5. CIRCUIT BREAKER
   ☐ Stop pipeline if 5+ failures in 1 hour
   ☐ Alert ops team immediately
   ☐ Require manual intervention to restart

6. LOGGING & DEBUGGING
   ☐ Log all errors to Application Insights
   ☐ Include context (RunId, Activity, Timestamp)
   ☐ Track data quality metrics
   ☐ Monitor function execution times

7. COST OPTIMIZATION
   ☐ Set reasonable timeouts (avoid billable hangs)
   ☐ Use exponential backoff (don't retry immediately)
   ☐ Monitor retry costs vs. reliability trade-off
   ☐ Consider manual retry for expensive operations

8. TESTING
   ☐ Test failure scenarios (network timeout, invalid data)
   ☐ Verify retry behavior
   ☐ Test notification delivery
   ☐ Simulate cascading failures
"""

print(RECOMMENDATIONS)

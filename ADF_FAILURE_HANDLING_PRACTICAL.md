# ADF Failure Handling: Practical Implementation Guide

## Quick Summary

This guide shows how to implement **retry policies**, **failure notifications**, and **monitoring alerts** for production-ready Azure Data Factory pipelines.

---

## 1. Retry Policy Configuration

### Problem
Without retries, any transient failure (timeout, throttling) causes the pipeline to fail immediately.

### Solution
Configure retry policies at the activity level.

```json
{
  "name": "BronzeIngestActivity",
  "type": "WebActivity",
  "typeProperties": {
    "method": "POST",
    "url": "https://func-app.azurewebsites.net/api/bronze-ingest",
    "body": {
      "storage_account": "stenvpipeline...",
      "container": "environmental-data",
      "csv_file": "landing/weather_raw.csv"
    }
  },
  "policy": {
    "timeout": "0.00:05:00",      # 5 minute timeout per attempt
    "retry": 3,                    # Retry 3 times total
    "retryIntervalInSeconds": 30   # Wait 30 seconds between retries
  }
}
```

### Timeline Example
```
Attempt 1: ❌ Fails at 2:30 PM
Wait 30 seconds...
Attempt 2: ❌ Fails at 2:31 PM
Wait 30 seconds...
Attempt 3: ❌ Fails at 2:32 PM
Wait 30 seconds...
Attempt 4: ❌ Fails at 2:33 PM
Pipeline FAILED after 4 total attempts
```

### Best Practices
- **Transient failures** (timeouts, 503 errors): Use 2-3 retries
- **Permanent failures** (authentication, data quality): Don't retry (wastes time & money)
- **Interval**: Start with 10-30 seconds; increase for long operations
- **Timeout**: Be reasonable (5m for Functions, 1h for aggregations)

---

## 2. On-Failure Notifications (Email)

### Problem
Pipeline fails silently → team doesn't know → data is stale → business impact

### Solution
Send email notification when activity fails.

### Step 1: Create Logic App (Email Handler)

In Azure Portal:
1. Create new Logic App → "Automated cloud flow" → HTTP trigger
2. Add action: "Send an email (V2)"
3. Copy the HTTP POST URL from the trigger
4. Use that URL in your ADF pipeline

### Step 2: Configure On-Failure Activity in ADF

```json
{
  "name": "BronzeIngestActivity",
  "type": "WebActivity",
  "typeProperties": {
    "method": "POST",
    "url": "https://func-app.azurewebsites.net/api/bronze-ingest",
    "body": {...}
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
            "url": "https://prod-123.logic.azure.com:443/workflows/.../triggers/manual/invoke?...",
            "body": {
              "subject": "ADF Pipeline Failed: Bronze Ingestion",
              "body": "Pipeline @{pipeline().RunId} failed\n\nError: @{activity('BronzeIngestActivity').Error.Message}"
            }
          }
        }
      ]
    }
  ]
}
```

### Example Email Output
```
Subject: ADF Pipeline Failed: Bronze Ingestion

Body:
Pipeline 1234567890 failed

Error: Azure Function returned HTTP 500: Internal Server Error
Time: 2024-01-15 14:30:45 UTC
Duration: 2 minutes 15 seconds
```

---

## 3. Slack Real-Time Alerts

### Problem
Email delays cause delayed response. Team might miss urgent failures.

### Solution
Send instant Slack notification for critical failures.

### Step 1: Get Slack Webhook

1. Go to Slack workspace settings
2. Create new app → "From scratch" → "Incoming Webhooks"
3. Enable and create new webhook
4. Copy webhook URL: `https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX`

### Step 2: Add Slack Notification Activity

```json
{
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
            "text": "*Pipeline:* orchestration_pipeline\n*Status:* ❌ Failed\n*Failed Activity:* @{activity('BronzeIngestActivity').ActivityName}\n*Error:* @{activity('BronzeIngestActivity').Error.Message}"
          }
        }
      ]
    }
  }
}
```

### Slack Message Output
```
🚨 Data Pipeline Failed

Pipeline: orchestration_pipeline
Status: ❌ Failed
Failed Activity: BronzeIngestActivity
Error: Function timed out after 5 minutes
```

---

## 4. Azure Monitor Alerts

### Problem
No centralized alerting → buried in logs → slower detection

### Solution
Create Azure Monitor metric alerts (sent to your Action Group).

### How It Works

```
1. Pipeline runs
2. If fails, metric is incremented
3. Monitor checks metric every 1 minute
4. If threshold exceeded, trigger alert
5. Alert sends email/Slack to Action Group
```

### Terraform Configuration
See `infra/terraform/adf_alerts.tf` for full implementation.

```hcl
# Create Action Group (notification destination)
resource "azurerm_monitor_action_group" "adf_failure_alerts" {
  name                = "ag-adf-failures-dev"
  resource_group_name = azurerm_resource_group.main.name
  short_name          = "ADF-FAIL"

  email_receiver {
    name          = "DataTeamEmail"
    email_address = "data-team@company.com"
  }
}

# Create alert rule
resource "azurerm_monitor_metric_alert" "adf_pipeline_failure" {
  name                = "adf-pipeline-failure-alert"
  resource_group_name = azurerm_resource_group.main.name
  scopes              = [azurerm_data_factory.main.id]
  
  criteria {
    metric_name = "PipelineFailedRuns"
    operator    = "GreaterThan"
    threshold   = 0
    aggregation = "Total"
    
    dimension {
      name     = "PipelineName"
      operator = "Include"
      values   = ["orchestration_pipeline"]
    }
  }

  action {
    action_group_id = azurerm_monitor_action_group.adf_failure_alerts.id
  }
}
```

---

## 5. Circuit Breaker Pattern

### Problem
If the Function is down, your pipeline will retry 3 times, fail, and lose data. Better to fail fast and stop.

### Solution
Check failure count before running pipeline. If too many recent failures, stop and alert ops.

```json
{
  "name": "CheckRecentFailures",
  "type": "Lookup",
  "typeProperties": {
    "source": {
      "type": "AzureSqlSource",
      "sqlReaderQuery": "SELECT COUNT(*) as FailureCount FROM dbo.PipelineRuns WHERE Status='Failed' AND CreatedDate >= DATEADD(hour,-1,GETDATE())"
    },
    "dataset": {
      "referenceName": "MonitoringDatabase",
      "type": "DatasetReference"
    }
  }
}
```

```json
{
  "name": "ShouldProceed",
  "type": "IfCondition",
  "typeProperties": {
    "expression": "@less(int(activity('CheckRecentFailures').output.firstRow.FailureCount), 5)",
    "ifFalseActivities": [
      {
        "name": "AlertCircuitBreakerTriggered",
        "type": "WebActivity",
        "typeProperties": {
          "method": "POST",
          "url": "https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
          "body": {
            "text": "🚨 CIRCUIT BREAKER TRIGGERED: 5+ failures in last hour. Pipeline halted. Manual intervention required."
          }
        }
      }
    ],
    "ifTrueActivities": [
      {
        "name": "BronzeIngestActivity",
        "type": "WebActivity",
        "typeProperties": {...}
      }
    ]
  }
}
```

---

## 6. Dead Letter Queue (Replay Failed Data)

### Problem
File fails to process → deleted/lost → can't retry

### Solution
Move failed files to dead letter queue for manual inspection & replay.

```json
{
  "name": "SendToDeadLetter",
  "type": "Copy",
  "dependsOn": [
    {
      "activity": "BronzeIngestActivity",
      "dependencyConditions": ["Failed"]
    }
  ],
  "inputs": [
    {
      "referenceName": "LandingBlobDataset",
      "type": "DatasetReference"
    }
  ],
  "outputs": [
    {
      "referenceName": "DeadLetterBlobDataset",
      "type": "DatasetReference",
      "parameters": {
        "folder": "dead-letter/@{formatDateTime(utcNow(), 'yyyy-MM-dd HH:mm')}"
      }
    }
  ]
}
```

**Result:**
```
landing/weather_raw.csv  →  ❌ Process fails  →  dead-letter/2024-01-15 14:30/weather_raw.csv
```

Later, ops team can:
1. Review the file in dead letter
2. Fix the issue (e.g., format error)
3. Move file back to landing
4. Re-run pipeline

---

## 7. Deployment Checklist

### Before Going to Production

```checklist
□ RETRY POLICIES
  □ Set retry count (2-3 for transient, 0 for permanent)
  □ Set timeout (appropriate for each operation)
  □ Set retry interval (10-30 seconds)

□ FAILURE NOTIFICATIONS
  □ Create Logic App for email (optional)
  □ Create Slack webhook URL
  □ Add OnFailure activity to each critical activity
  □ Test failure path manually

□ MONITORING
  □ Create Action Group with email receivers
  □ Create metric alert for pipeline failures
  □ Create metric alert for activity failures
  □ Set up Log Analytics workspace
  □ Enable diagnostic settings on Data Factory

□ DATA PROTECTION
  □ Create dead letter queue path in ADLS
  □ Add Copy activity for failed messages
  □ Document replay procedure
  □ Test dead letter retrieval

□ CIRCUIT BREAKER (Optional for prod)
  □ Create monitoring database
  □ Add failure count check activity
  □ Add IfCondition for circuit breaker
  □ Create escalation alert (Slack/email)

□ TESTING
  □ Test retry behavior (simulate timeout)
  □ Test on-failure email/Slack
  □ Test dead letter handling
  □ Verify metrics in Monitor
```

---

## 8. Cost Optimization

### Retry Cost
```
Each retry = 1 full pipeline run

Example:
  Initial run: ❌ $0.50
  Retry 1:     ❌ $0.50
  Retry 2:     ❌ $0.50
  Retry 3:     ✅ $0.50
  Total cost: $2.00 (4x normal)
```

**Best Practice:** Only retry transient failures
- ✅ Retry: Network timeout, 503 Service Unavailable, 429 Throttled
- ❌ Don't retry: Authentication failure, Invalid input, File not found

### Timeout Cost
```
If timeout set to 24 hours and job hangs:
  - You'll be billed for full 24 hours
  - Smart timeout = 1-2 hours max
```

**Best Practice:** Set reasonable timeouts
- 5 minutes: Azure Functions (fast operations)
- 1 hour: Data transformations
- 24 hours: Large aggregations only

---

## 9. Example: Complete Production Pipeline

```json
{
  "name": "orchestration_pipeline",
  "properties": {
    "activities": [
      {
        "name": "BronzeIngestActivity",
        "type": "WebActivity",
        "policy": {
          "timeout": "0.00:05:00",
          "retry": 2,
          "retryIntervalInSeconds": 30
        },
        "typeProperties": {
          "method": "POST",
          "url": "https://func-app.azurewebsites.net/api/bronze-ingest",
          "body": {...}
        },
        "onFailure": [
          {
            "activities": [
              {
                "name": "NotifySlackBronzeFailure",
                "type": "WebActivity",
                "typeProperties": {
                  "method": "POST",
                  "url": "YOUR_SLACK_WEBHOOK_URL",
                  "body": {
                    "text": "❌ Bronze ingestion failed"
                  }
                }
              },
              {
                "name": "SendToBronzeDeadLetter",
                "type": "Copy",
                "inputs": [{"referenceName": "LandingDataset"}],
                "outputs": [{"referenceName": "DeadLetterDataset"}]
              }
            ]
          }
        ]
      },
      {
        "name": "SilverTransformActivity",
        "dependsOn": [{"activity": "BronzeIngestActivity", "dependencyConditions": ["Succeeded"]}],
        "policy": {
          "timeout": "0.00:10:00",
          "retry": 1,
          "retryIntervalInSeconds": 60
        },
        "type": "WebActivity",
        "typeProperties": {
          "method": "POST",
          "url": "https://func-app.azurewebsites.net/api/silver-transform",
          "body": {...}
        },
        "onFailure": [
          {
            "activities": [
              {
                "name": "NotifySlackSilverFailure",
                "type": "WebActivity",
                "typeProperties": {
                  "method": "POST",
                  "url": "YOUR_SLACK_WEBHOOK_URL",
                  "body": {
                    "text": "❌ Silver transformation failed"
                  }
                }
              }
            ]
          }
        ]
      },
      {
        "name": "GoldTransformActivity",
        "dependsOn": [{"activity": "SilverTransformActivity", "dependencyConditions": ["Succeeded"]}],
        "policy": {
          "timeout": "0.01:00:00",
          "retry": 0
        },
        "type": "WebActivity",
        "typeProperties": {
          "method": "POST",
          "url": "https://func-app.azurewebsites.net/api/gold-transform",
          "body": {...}
        },
        "onSuccess": [
          {
            "activities": [
              {
                "name": "NotifySlackSuccess",
                "type": "WebActivity",
                "typeProperties": {
                  "method": "POST",
                  "url": "YOUR_SLACK_WEBHOOK_URL",
                  "body": {
                    "text": "✅ Pipeline completed successfully"
                  }
                }
              }
            ]
          }
        ]
      }
    ]
  }
}
```

---

## 10. Debugging Failed Pipeline

### Step 1: Find the Run
1. Go to Data Factory → Monitor → Pipeline runs
2. Find your failed pipeline run
3. Click on it to see timeline

### Step 2: Identify Failed Activity
- Green = succeeded
- Red = failed
- Click red activity to see details

### Step 3: Check Error Message
The error message tells you what went wrong:
- `"Function timed out"` → Increase timeout or optimize code
- `"Authentication failed"` → Check credentials/managed identity
- `"Function returned 500"` → Check Function logs in App Insights
- `"Connection timeout"` → Check network/firewall rules

### Step 4: Check Detailed Logs
1. Click on failed activity
2. Go to "Diagnostics" tab
3. Look at full error stack

### Step 5: Check Function Logs
1. Go to Function App → Functions → bronze-ingest
2. Go to "Monitor" tab
3. Filter by recent runs
4. Click on failed invocation
5. See full logs in Application Insights

---

## 11. Support Matrix

| Issue | Cause | Solution |
|-------|-------|----------|
| Timeout | Function takes >5min | Increase timeout or optimize code |
| 503 Service Unavailable | Azure throttling | Reduce concurrency, use backoff |
| 401 Unauthorized | Bad credentials | Check managed identity RBAC |
| Invalid input | Bad JSON | Validate body schema |
| File not found | Wrong path | Verify ADLS path structure |
| Retry loop | Retrying too much | Check retry policy, may cost more |
| Silent failure | No logs | Enable diagnostics, check App Insights |

---

## 12. Next Steps

1. **Deploy alerts** (run Terraform with new `adf_alerts.tf`)
2. **Configure email** (update `alert_email_address` in `terraform.tfvars`)
3. **Set up Slack** (optional, add webhook URL)
4. **Test failure** (manually invoke with invalid data)
5. **Monitor results** (check Azure Monitor and email/Slack notifications)
6. **Document runbooks** (how to handle each failure type)

---

## Resources

- [ADF Failure Handling JSON Examples](./ADF_FAILURE_HANDLING.md) - Complete code samples
- [Terraform Alert Configuration](./infra/terraform/adf_alerts.tf) - Infrastructure as code
- [Azure Monitor Documentation](https://docs.microsoft.com/en-us/azure/azure-monitor/)
- [ADF Activity Dependencies](https://docs.microsoft.com/en-us/azure/data-factory/concepts-pipelines-activities)

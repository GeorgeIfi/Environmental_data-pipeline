# Synapse SQL: Business Intelligence Queries Guide

## Overview

This guide explains the business-focused SQL queries in the Environmental Data Pipeline. These queries analyze the **Gold layer** data to answer key business questions about air quality, pollution trends, compliance, and health implications.

---

## Quick Reference: Top 10 Most Useful Queries

| Query | Purpose | Business Value |
|-------|---------|-----------------|
| **2.1** | Current Pollution Levels | Real-time air quality dashboard |
| **2.2** | 7-Day Trend | Is pollution improving or worsening? |
| **3.1** | Cleanest vs. Dirtiest Locations | Identify hotspots for intervention |
| **3.2** | Zone Comparison | Compare urban vs. rural areas |
| **4.1** | Anomaly Detection | Early warning system for spikes |
| **6.1** | Days Exceeding Limits | Regulatory compliance tracking |
| **6.2** | Compliance Status | Monthly/quarterly reporting |
| **5.1** | Weekday vs. Weekend | Understand pollution sources (traffic?) |
| **5.3** | Month-over-Month Growth | Long-term improvement tracking |
| **8.1** | Executive Summary | Board/stakeholder reporting |

---

## Query Categories & Use Cases

### 1. **Data Quality & Completeness Checks**

**When to use:** Data governance, data pipeline validation

- **Query 1.1**: Overall data quality summary
  - ✅ Shows data freshness
  - ✅ Checks completeness rate
  - ✅ Validates medallion layer transformations

- **Query 1.2**: Data availability by location
  - ✅ Identifies locations with incomplete data
  - ✅ Flags monitoring gaps
  - ✅ Plan maintenance or equipment replacement

- **Query 1.3**: Missing data detection
  - ✅ Find exact date/location/pollutant gaps
  - ✅ Prioritize data collection efforts
  - ✅ Validate SLA compliance

**Business Impact:** Ensures data accuracy for decision-making

---

### 2. **Pollution Level Analysis & Trends**

**When to use:** Health reporting, air quality monitoring, public communication

- **Query 2.1**: Current pollution levels by location
  - ✅ Real-time air quality status
  - ✅ Health implications (Unhealthy/Moderate/Healthy)
  - ✅ Basis for public health alerts

- **Query 2.2**: 7-Day pollution trend
  - ✅ Track if pollution is improving
  - ✅ Measure effectiveness of policy changes
  - ✅ Compare locations

- **Query 2.3**: Highest pollution days
  - ✅ Identify worst-case scenarios
  - ✅ Root cause analysis
  - ✅ Pattern recognition (time of year, weather?)

- **Query 2.4**: Monthly pollution comparison
  - ✅ Year-over-year trends
  - ✅ Seasonal patterns
  - ✅ Volatility analysis

**Business Impact:** Drives public health policy decisions

---

### 3. **Location-Based Analysis**

**When to use:** Urban planning, environmental justice, resource allocation

- **Query 3.1**: Cleanest vs. Dirtiest locations
  - ✅ Identify pollution hotspots
  - ✅ Priority areas for intervention
  - ✅ Compare cities/neighborhoods

- **Query 3.2**: Zone comparison (urban vs. rural)
  - ✅ Understand geographic patterns
  - ✅ Validate urbanization impact
  - ✅ Cross-regional benchmarking

- **Query 3.3**: Location performance scorecard
  - ✅ Simple letter grade (Good/Moderate/Poor)
  - ✅ Quick visual dashboard
  - ✅ Accountability tracking

**Business Impact:** Data-driven urban planning and environmental justice

---

### 4. **Statistical Analysis & Outliers**

**When to use:** Data science, anomaly detection, quality control

- **Query 4.1**: Anomaly detection (unusual spikes)
  - ✅ Automatic spike detection
  - ✅ Early warning system
  - ✅ Equipment malfunction detection

- **Query 4.2**: Percentile analysis
  - ✅ Understand data distribution
  - ✅ Set realistic targets (e.g., "reduce P90 by 20%")
  - ✅ Forecast confidence estimation

**Business Impact:** Proactive issue detection, data quality assurance

---

### 5. **Time-Based Analysis**

**When to use:** Pattern recognition, policy evaluation

- **Query 5.1**: Weekday vs. Weekend patterns
  - ✅ Identify if traffic causes pollution
  - ✅ Evaluate rush-hour policies
  - ✅ Predict demand for interventions

- **Query 5.2**: Seasonal trends
  - ✅ Expected winter worsening
  - ✅ Spring improvement
  - ✅ Plan seasonal interventions

- **Query 5.3**: Month-over-month growth/decline
  - ✅ Track progress toward targets
  - ✅ Measure policy effectiveness
  - ✅ Identify improvement/degradation

**Business Impact:** Policy evaluation, performance tracking

---

### 6. **Compliance & Regulatory Analysis**

**When to use:** Government reporting, legal compliance, audits

- **Query 6.1**: Days exceeding limits
  - ✅ Regulatory violation tracking
  - ✅ Fines/penalty forecasting
  - ✅ Legal defensibility

- **Query 6.2**: Regulatory compliance status
  - ✅ Monthly/quarterly compliance reports
  - ✅ Certification audit support
  - ✅ Stakeholder transparency

**Business Impact:** Legal compliance, public accountability

---

### 7. **Predictive & Forecasting Prep**

**When to use:** Forecasting models, machine learning setup

- **Query 7.1**: Data volatility
  - ✅ High volatility = harder to forecast
  - ✅ Determines forecast model choice
  - ✅ Estimates confidence intervals

- **Query 7.2**: Trend direction
  - ✅ Automated trend detection
  - ✅ Basis for predictive models
  - ✅ Extrapolate into future

**Business Impact:** Supports advanced analytics and AI/ML models

---

### 8. **Executive Summary Dashboard**

**When to use:** Board meetings, stakeholder reports, PR

- **Query 8.1**: Key metrics summary
  - ✅ One-page executive overview
  - ✅ Green/red status indicators
  - ✅ Highest-risk areas highlighted

- **Query 8.2**: Monthly compliance report
  - ✅ Regulatory reporting
  - ✅ Stakeholder communication
  - ✅ Trend visualization

**Business Impact:** Executive visibility, accountability

---

## Setup Instructions

### Step 1: Connect to Synapse

```sql
-- Connect to your Synapse Dedicated SQL Pool or Serverless SQL Pool
-- Select database: [adf-environmental] or equivalent
```

### Step 2: Create External Table (if needed)

If your gold data is in ADLS as parquet files:

```sql
CREATE EXTERNAL DATA SOURCE ds_datalake
WITH (
    TYPE = HADOOP,
    LOCATION = 'abfss://environmental-data@stenvpipeline....dfs.core.windows.net'
);

CREATE EXTERNAL FILE FORMAT ff_parquet
WITH (
    FORMAT_TYPE = PARQUET,
    DATA_COMPRESSION = 'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe'
);

CREATE EXTERNAL TABLE gold_weather (
    [date] DATE,
    [location] VARCHAR(100),
    [latitude] FLOAT,
    [longitude] FLOAT,
    [zone] VARCHAR(50),
    [pollutant_type] VARCHAR(50),
    [avg_value] FLOAT,
    [max_value] FLOAT,
    [min_value] FLOAT,
    [record_count] INT
)
WITH (
    LOCATION = 'gold/weather/',
    DATA_SOURCE = ds_datalake,
    FILE_FORMAT = ff_parquet
);
```

### Step 3: Run Queries

Copy any query from `06_business_analytics.sql` and execute:

```sql
-- Example: Get current pollution levels
SELECT
    location,
    date,
    pollutant_type,
    ROUND(avg_value, 2) AS AvgLevel,
    CASE
        WHEN pollutant_type = 'PM2.5' AND avg_value > 35.4 THEN 'UNHEALTHY'
        WHEN pollutant_type = 'PM2.5' AND avg_value > 12 THEN 'MODERATE'
        ELSE 'HEALTHY'
    END AS HealthStatus
FROM gold_weather
WHERE date = (SELECT MAX(date) FROM gold_weather)
ORDER BY location, pollutant_type;
```

---

## Real-World Examples

### Example 1: Public Health Alert

**Scenario:** City wants to alert residents about poor air quality

```sql
-- Check if any location exceeds thresholds
SELECT location, pollutant_type, avg_value, 'ALERT' AS Status
FROM gold_weather
WHERE date = CAST(GETDATE() AS DATE)
  AND ((pollutant_type = 'PM2.5' AND avg_value > 35.4)
    OR (pollutant_type = 'NO2' AND avg_value > 200));
```

**Result:**
```
London    | PM2.5  | 42.1 | ALERT
```

**Action:** Issue public health warning, recommend reducing outdoor activity

---

### Example 2: Compliance Audit

**Scenario:** Regulatory authority needs to verify compliance

```sql
-- Monthly compliance report for Q4 2024
SELECT
    DATEFROMPARTS(YEAR(date), MONTH(date), 1) AS Month,
    COUNT(DISTINCT location) AS Locations,
    COUNT(DISTINCT date) AS DataDays,
    SUM(CASE WHEN avg_value > 35.4 THEN 1 ELSE 0 END) AS ExceedanceDays,
    ROUND(100.0 * SUM(CASE WHEN avg_value > 35.4 THEN 1 ELSE 0 END) / COUNT(*), 2) AS ExceedanceRate
FROM gold_weather
WHERE YEAR(date) = 2024 AND MONTH(date) >= 10
GROUP BY YEAR(date), MONTH(date)
ORDER BY MONTH DESC;
```

**Result:**
```
2024-10-01 | 5 | 31 | 2 | 6.45%  ← Compliant
2024-11-01 | 5 | 30 | 5 | 16.67% ← Warning
2024-12-01 | 5 | 31 | 8 | 25.81% ← Non-compliant
```

**Action:** Initiate air quality improvement campaign before Q1 audit

---

### Example 3: Policy Evaluation

**Scenario:** Government implemented "No-Smoke Tuesday" to reduce vehicle emissions

```sql
-- Compare Tuesday vs. other weekdays
SELECT
    CASE DATEPART(WEEKDAY, date)
        WHEN 2 THEN 'Monday'
        WHEN 3 THEN 'Tuesday (No-Smoke)'
        WHEN 4 THEN 'Wednesday'
        WHEN 5 THEN 'Thursday'
        WHEN 6 THEN 'Friday'
    END AS Day,
    ROUND(AVG(avg_value), 2) AS AvgNO2
FROM gold_weather
WHERE pollutant_type = 'NO2'
  AND date >= DATEADD(MONTH, -6, CAST(GETDATE() AS DATE))
GROUP BY DATEPART(WEEKDAY, date)
ORDER BY DATEPART(WEEKDAY, date);
```

**Result:**
```
Monday      | 89.2 µg/m³
Tuesday     | 72.4 µg/m³  ← 18.8% reduction!
Wednesday   | 91.1 µg/m³
Thursday    | 92.5 µg/m³
Friday      | 95.3 µg/m³
```

**Conclusion:** Policy is working! Recommend making it permanent or expanding.

---

### Example 4: Anomaly Detection (Equipment Failure)

**Scenario:** Sensor malfunctioning, reporting unrealistic values

```sql
-- Find unusual spikes in PM2.5
SELECT TOP 5
    location,
    date,
    avg_value,
    Rolling30DayAvg,
    CASE
        WHEN avg_value > Rolling30DayAvg * 3 THEN 'LIKELY EQUIPMENT FAILURE'
        WHEN avg_value > Rolling30DayAvg * 2 THEN 'INVESTIGATE'
        ELSE 'NORMAL'
    END AS Alert
FROM (
    SELECT
        location,
        date,
        avg_value,
        AVG(avg_value) OVER (
            PARTITION BY location 
            ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        ) AS Rolling30DayAvg
    FROM gold_weather
    WHERE pollutant_type = 'PM2.5'
) x
ORDER BY avg_value DESC;
```

**Result:**
```
Manchester | 2024-01-15 | 156.2 | 38.5 | LIKELY EQUIPMENT FAILURE
```

**Action:** Dispatch technician to check sensor at Manchester site

---

## Performance Tips

### For Large Datasets (>1 year of data)

1. **Add date filters:** Always filter to last N days
   ```sql
   WHERE date >= DATEADD(MONTH, -3, CAST(GETDATE() AS DATE))
   ```

2. **Use TOP N:** Limit result sets
   ```sql
   SELECT TOP 1000 * FROM gold_weather...
   ```

3. **Aggregate first:** Pre-aggregate before joining
   ```sql
   SELECT location, pollutant_type, ROUND(AVG(avg_value), 2) AS AvgLevel
   FROM gold_weather
   GROUP BY location, pollutant_type
   ```

4. **Materialized Views:** For frequently-used queries
   ```sql
   CREATE MATERIALIZED VIEW vw_monthly_summary AS
   SELECT YEAR(date) AS Year, MONTH(date) AS Month, ...
   FROM gold_weather
   GROUP BY YEAR(date), MONTH(date)...
   ```

---

## Integration with Power BI

To visualize these queries in Power BI:

1. In Power BI Desktop, create new query
2. Use "Azure Synapse Analytics" connector
3. Paste query directly into Power Query Editor
4. Create visualizations (line charts, heatmaps, etc.)
5. Set up automatic refresh schedule

**Recommended Visuals:**
- **Line Chart:** Pollution trend (Query 2.2)
- **Map:** Location pollution levels (Query 3.1)
- **Card:** Current status (Query 2.1)
- **Bar Chart:** Zone comparison (Query 3.2)
- **Table:** Anomalies (Query 4.1)

---

## Scheduling & Automation

Use Azure Data Factory to:

1. **Schedule monthly compliance reports**
   ```
   Activity type: Synapse SQL pool
   Stored procedure: [dbo].[sp_monthly_compliance_report]
   Frequency: Monthly, 1st day at 6 AM
   ```

2. **Automated anomaly alerts**
   ```
   Activity type: Synapse SQL pool
   Query: Query 4.1 (Anomaly detection)
   If result count > 0, send email alert
   ```

3. **Export to data warehouse**
   ```
   Activity type: Copy
   Source: Synapse SQL
   Sink: Azure SQL Database
   Schedule: Daily
   ```

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| "gold_weather table not found" | External table not created | Run CREATE EXTERNAL TABLE statement |
| "Query timeout" | Too much data selected | Add date filter, reduce date range |
| "NULL values in results" | Missing data | Use Query 1.3 to find gaps |
| "Inconsistent counts" | Aggregation mismatch | Verify GROUP BY clauses |
| "Slow performance" | Large dataset scan | Create materialized view or aggregate first |

---

## Best Practices

✅ **DO:**
- Always filter by date to limit data scope
- Use meaningful column aliases for clarity
- Add comments explaining business logic
- Test on small date ranges first
- Schedule maintenance during off-peak hours

❌ **DON'T:**
- Run SELECT * without filters
- Join large tables without aggregation
- Ignore NULL values
- Hardcode thresholds (use parameters instead)
- Run long-running queries during peak hours

---

## Next Steps

1. **Copy queries** from `06_business_analytics.sql`
2. **Adapt thresholds** to your region's air quality standards
3. **Add more pollutants** as data becomes available
4. **Integrate with Power BI** for visualization
5. **Schedule automated reports** in Data Factory
6. **Set up alerts** for anomalies and compliance violations

---

## Support

For issues or custom queries, refer to:
- [Synapse SQL Documentation](https://learn.microsoft.com/en-us/azure/synapse-analytics/)
- [ADF Documentation](https://learn.microsoft.com/en-us/azure/data-factory/)
- Project repository: Environmental Data Pipeline


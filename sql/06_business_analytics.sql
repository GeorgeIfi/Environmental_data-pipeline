-- ============================================================================
-- SYNAPSE SQL: Business Intelligence Queries
-- Environmental Data Pipeline - Gold Layer Analysis
-- ============================================================================
-- These queries analyze the processed environmental data in the Gold layer
-- Use against Azure Synapse Dedicated SQL Pool or Serverless SQL Pool
-- ============================================================================

-- ============================================================================
-- 1. DATA QUALITY & COMPLETENESS CHECKS
-- ============================================================================

-- 1.1: Overall Data Quality Summary
-- Shows completeness, coverage, and data freshness
SELECT
    COUNT(DISTINCT date) AS UniqueDataDays,
    COUNT(DISTINCT location) AS UniqueLocations,
    COUNT(DISTINCT pollutant_type) AS PolluantTypes,
    MIN(date) AS EarliestDate,
    MAX(date) AS LatestDate,
    DATEDIFF(DAY, MIN(date), MAX(date)) + 1 AS DataCoverageDays,
    COUNT(*) AS TotalRecords,
    ROUND(COUNT(*) / CAST(COUNT(DISTINCT date) * COUNT(DISTINCT location) * COUNT(DISTINCT pollutant_type) AS FLOAT), 4) AS CompletionRate
FROM gold_weather
WHERE date >= DATEADD(DAY, -90, CAST(GETDATE() AS DATE));

-- 1.2: Data Availability by Location
-- Identifies locations with gaps in data collection
SELECT
    location,
    COUNT(DISTINCT date) AS DaysOfData,
    COUNT(DISTINCT pollutant_type) AS AvailablePollutants,
    MIN(date) AS FirstDate,
    MAX(date) AS LastDate,
    DATEDIFF(DAY, MIN(date), MAX(date)) + 1 AS PotentialDays,
    ROUND(100.0 * COUNT(DISTINCT date) / (DATEDIFF(DAY, MIN(date), MAX(date)) + 1), 2) AS DataCoveragePercent
FROM gold_weather
GROUP BY location
ORDER BY DataCoveragePercent DESC;

-- 1.3: Missing Data Detection (Data Gaps)
-- Shows which date/location/pollutant combinations are missing
WITH DateRange AS (
    SELECT DISTINCT date
    FROM gold_weather
),
LocationPollutants AS (
    SELECT DISTINCT location, pollutant_type
    FROM gold_weather
),
ExpectedRecords AS (
    SELECT d.date, l.location, l.pollutant_type
    FROM DateRange d
    CROSS JOIN LocationPollutants l
),
ActualRecords AS (
    SELECT DISTINCT date, location, pollutant_type
    FROM gold_weather
)
SELECT
    e.date,
    e.location,
    e.pollutant_type,
    CASE WHEN a.date IS NULL THEN 'MISSING' ELSE 'PRESENT' END AS DataStatus,
    DATEDIFF(DAY, e.date, GETDATE()) AS DaysAgo
FROM ExpectedRecords e
LEFT JOIN ActualRecords a 
    ON e.date = a.date 
    AND e.location = a.location 
    AND e.pollutant_type = a.pollutant_type
WHERE a.date IS NULL
ORDER BY e.date DESC, e.location, e.pollutant_type;

-- ============================================================================
-- 2. POLLUTION LEVEL ANALYSIS & TRENDS
-- ============================================================================

-- 2.1: Current Pollution Levels by Location (Latest Day)
-- Shows most recent pollution measurements with health implications
SELECT
    location,
    date,
    pollutant_type,
    ROUND(avg_value, 2) AS AvgLevel,
    ROUND(min_value, 2) AS MinLevel,
    ROUND(max_value, 2) AS MaxLevel,
    record_count AS MeasurementCount,
    CASE
        WHEN pollutant_type = 'PM2.5' AND avg_value > 35.4 THEN 'UNHEALTHY'
        WHEN pollutant_type = 'PM2.5' AND avg_value > 12 THEN 'MODERATE'
        WHEN pollutant_type = 'NO2' AND avg_value > 200 THEN 'UNHEALTHY'
        WHEN pollutant_type = 'NO2' AND avg_value > 100 THEN 'MODERATE'
        ELSE 'HEALTHY'
    END AS HealthStatus
FROM gold_weather
WHERE date = (SELECT MAX(date) FROM gold_weather)
ORDER BY location, pollutant_type;

-- 2.2: 7-Day Pollution Trend
-- Shows if pollution is improving or worsening over past week
SELECT
    location,
    pollutant_type,
    date,
    ROUND(avg_value, 2) AS AvgLevel,
    LAG(ROUND(avg_value, 2)) OVER (
        PARTITION BY location, pollutant_type 
        ORDER BY date
    ) AS PreviousDayAvg,
    ROUND(
        (avg_value - LAG(avg_value) OVER (PARTITION BY location, pollutant_type ORDER BY date)) / 
        LAG(avg_value) OVER (PARTITION BY location, pollutant_type ORDER BY date) * 100, 
        2
    ) AS PercentChange,
    CASE
        WHEN avg_value > LAG(avg_value) OVER (PARTITION BY location, pollutant_type ORDER BY date) THEN 'WORSENING'
        WHEN avg_value < LAG(avg_value) OVER (PARTITION BY location, pollutant_type ORDER BY date) THEN 'IMPROVING'
        ELSE 'STABLE'
    END AS Trend
FROM gold_weather
WHERE date >= DATEADD(DAY, -7, CAST(GETDATE() AS DATE))
ORDER BY location, pollutant_type, date DESC;

-- 2.3: Highest Pollution Days (Exceedances)
-- Identifies days when pollution exceeded WHO guidelines
SELECT TOP 20
    date,
    location,
    pollutant_type,
    ROUND(max_value, 2) AS MaxLevel,
    ROUND(avg_value, 2) AS AvgLevel,
    record_count,
    CASE
        WHEN pollutant_type = 'PM2.5' AND avg_value > 35.4 THEN 'UNHEALTHY'
        WHEN pollutant_type = 'PM2.5' AND avg_value > 12 THEN 'MODERATE'
        WHEN pollutant_type = 'NO2' AND avg_value > 200 THEN 'UNHEALTHY'
        WHEN pollutant_type = 'NO2' AND avg_value > 100 THEN 'MODERATE'
        ELSE 'HEALTHY'
    END AS HealthRating
FROM gold_weather
WHERE (pollutant_type = 'PM2.5' AND avg_value > 12) 
   OR (pollutant_type = 'NO2' AND avg_value > 100)
ORDER BY date DESC, max_value DESC;

-- 2.4: Monthly Pollution Comparison (Year-over-Year if available)
-- Shows seasonal patterns and year-on-year trends
SELECT
    YEAR(date) AS Year,
    MONTH(date) AS Month,
    pollutant_type,
    COUNT(DISTINCT location) AS LocationsMonitored,
    ROUND(AVG(avg_value), 2) AS AvgMonthlyLevel,
    ROUND(MIN(min_value), 2) AS MonthlyMin,
    ROUND(MAX(max_value), 2) AS MonthlyMax,
    ROUND(STDEV(avg_value), 2) AS Volatility
FROM gold_weather
GROUP BY YEAR(date), MONTH(date), pollutant_type
ORDER BY Year DESC, Month DESC, pollutant_type;

-- ============================================================================
-- 3. LOCATION-BASED ANALYSIS
-- ============================================================================

-- 3.1: Cleanest vs. Dirtiest Locations
-- Rankings of locations by overall air quality
WITH LocationStats AS (
    SELECT
        location,
        zone,
        pollutant_type,
        ROUND(AVG(avg_value), 2) AS AvgLevel,
        ROUND(MAX(max_value), 2) AS MaxLevel,
        COUNT(DISTINCT date) AS DataDays,
        ROW_NUMBER() OVER (PARTITION BY pollutant_type ORDER BY AVG(avg_value) DESC) AS RankDirtiest,
        ROW_NUMBER() OVER (PARTITION BY pollutant_type ORDER BY AVG(avg_value) ASC) AS RankCleanest
    FROM gold_weather
    WHERE date >= DATEADD(DAY, -30, CAST(GETDATE() AS DATE))
    GROUP BY location, zone, pollutant_type
)
SELECT
    'CLEANEST' AS Ranking,
    location,
    zone,
    pollutant_type,
    AvgLevel,
    MaxLevel,
    DataDays,
    RankCleanest AS Rank
FROM LocationStats
WHERE RankCleanest <= 5
UNION ALL
SELECT
    'DIRTIEST' AS Ranking,
    location,
    zone,
    pollutant_type,
    AvgLevel,
    MaxLevel,
    DataDays,
    RankDirtiest AS Rank
FROM LocationStats
WHERE RankDirtiest <= 5
ORDER BY Ranking, Rank;

-- 3.2: Zone Comparison
-- Compares air quality across geographic zones
SELECT
    zone,
    pollutant_type,
    COUNT(DISTINCT location) AS LocationsInZone,
    COUNT(DISTINCT date) AS DaysOfData,
    ROUND(AVG(avg_value), 2) AS AvgLevel,
    ROUND(MIN(min_value), 2) AS MinLevel,
    ROUND(MAX(max_value), 2) AS MaxLevel,
    ROUND(STDEV(avg_value), 2) AS Volatility,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY avg_value) OVER (PARTITION BY zone, pollutant_type), 2) AS Median
FROM gold_weather
WHERE date >= DATEADD(DAY, -90, CAST(GETDATE() AS DATE))
GROUP BY zone, pollutant_type
ORDER BY zone, pollutant_type;

-- 3.3: Location Performance Scorecard
-- Composite score showing location health status
WITH LocationMetrics AS (
    SELECT
        location,
        zone,
        ROUND(AVG(CASE WHEN pollutant_type = 'PM2.5' THEN avg_value ELSE NULL END), 2) AS PM25_Avg,
        ROUND(AVG(CASE WHEN pollutant_type = 'NO2' THEN avg_value ELSE NULL END), 2) AS NO2_Avg,
        ROUND(AVG(avg_value), 2) AS OverallAvg,
        COUNT(DISTINCT date) AS DataPoints
    FROM gold_weather
    WHERE date >= DATEADD(DAY, -30, CAST(GETDATE() AS DATE))
    GROUP BY location, zone
)
SELECT
    location,
    zone,
    PM25_Avg,
    NO2_Avg,
    OverallAvg,
    DataPoints,
    CASE
        WHEN (ISNULL(PM25_Avg, 0) <= 12 OR PM25_Avg IS NULL) 
         AND (ISNULL(NO2_Avg, 0) <= 100 OR NO2_Avg IS NULL) THEN 'GOOD'
        WHEN (ISNULL(PM25_Avg, 0) <= 35.4 OR PM25_Avg IS NULL) 
         AND (ISNULL(NO2_Avg, 0) <= 200 OR NO2_Avg IS NULL) THEN 'MODERATE'
        ELSE 'POOR'
    END AS AirQualityGrade
FROM LocationMetrics
ORDER BY OverallAvg DESC;

-- ============================================================================
-- 4. STATISTICAL ANALYSIS & OUTLIERS
-- ============================================================================

-- 4.1: Anomaly Detection (Unusual Pollution Spikes)
-- Identifies measurements that deviate significantly from normal
WITH Stats AS (
    SELECT
        location,
        pollutant_type,
        date,
        avg_value,
        AVG(avg_value) OVER (
            PARTITION BY location, pollutant_type 
            ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        ) AS Rolling30DayAvg,
        STDEV(avg_value) OVER (
            PARTITION BY location, pollutant_type 
            ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        ) AS Rolling30DayStdDev
    FROM gold_weather
    WHERE date >= DATEADD(DAY, -60, CAST(GETDATE() AS DATE))
)
SELECT
    date,
    location,
    pollutant_type,
    ROUND(avg_value, 2) AS ObservedValue,
    ROUND(Rolling30DayAvg, 2) AS Expected30DayAvg,
    ROUND(Rolling30DayStdDev, 2) AS Volatility,
    ROUND(ABS(avg_value - Rolling30DayAvg) / NULLIF(Rolling30DayStdDev, 0), 2) AS StandardDeviations,
    CASE
        WHEN ABS(avg_value - Rolling30DayAvg) / NULLIF(Rolling30DayStdDev, 0) > 2.5 THEN 'ANOMALY'
        WHEN ABS(avg_value - Rolling30DayAvg) / NULLIF(Rolling30DayStdDev, 0) > 2 THEN 'UNUSUAL'
        ELSE 'NORMAL'
    END AS AnomalyStatus
FROM Stats
WHERE Rolling30DayStdDev IS NOT NULL
  AND ABS(avg_value - Rolling30DayAvg) / NULLIF(Rolling30DayStdDev, 0) > 1.5
ORDER BY date DESC, StandardDeviations DESC;

-- 4.2: Percentile Analysis (Distribution)
-- Shows how measurements are distributed (P10, P25, Median, P75, P90)
SELECT
    location,
    pollutant_type,
    ROUND(PERCENTILE_CONT(0.10) WITHIN GROUP (ORDER BY avg_value) OVER (PARTITION BY location, pollutant_type), 2) AS P10,
    ROUND(PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY avg_value) OVER (PARTITION BY location, pollutant_type), 2) AS P25,
    ROUND(PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY avg_value) OVER (PARTITION BY location, pollutant_type), 2) AS Median,
    ROUND(PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY avg_value) OVER (PARTITION BY location, pollutant_type), 2) AS P75,
    ROUND(PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY avg_value) OVER (PARTITION BY location, pollutant_type), 2) AS P90,
    ROUND(AVG(avg_value) OVER (PARTITION BY location, pollutant_type), 2) AS Mean
FROM gold_weather
WHERE date >= DATEADD(DAY, -90, CAST(GETDATE() AS DATE))
GROUP BY location, pollutant_type, avg_value;

-- ============================================================================
-- 5. TIME-BASED ANALYSIS
-- ============================================================================

-- 5.1: Daily Patterns (Weekday vs Weekend)
-- Shows if pollution differs on weekdays vs weekends
SELECT
    CASE DATEPART(WEEKDAY, date)
        WHEN 1 THEN 'Sunday'
        WHEN 2 THEN 'Monday'
        WHEN 3 THEN 'Tuesday'
        WHEN 4 THEN 'Wednesday'
        WHEN 5 THEN 'Thursday'
        WHEN 6 THEN 'Friday'
        WHEN 7 THEN 'Saturday'
    END AS DayOfWeek,
    CASE WHEN DATEPART(WEEKDAY, date) IN (1, 7) THEN 'Weekend' ELSE 'Weekday' END AS IsWeekend,
    pollutant_type,
    COUNT(DISTINCT location) AS LocationsMonitored,
    ROUND(AVG(avg_value), 2) AS AvgLevel,
    ROUND(MAX(max_value), 2) AS PeakLevel,
    COUNT(*) AS ObservationCount
FROM gold_weather
WHERE date >= DATEADD(DAY, -90, CAST(GETDATE() AS DATE))
GROUP BY DATEPART(WEEKDAY, date), pollutant_type
ORDER BY DATEPART(WEEKDAY, date), pollutant_type;

-- 5.2: Seasonal Trends
-- Shows pollution patterns by season
SELECT
    CASE
        WHEN MONTH(date) IN (12, 1, 2) THEN 'Winter'
        WHEN MONTH(date) IN (3, 4, 5) THEN 'Spring'
        WHEN MONTH(date) IN (6, 7, 8) THEN 'Summer'
        WHEN MONTH(date) IN (9, 10, 11) THEN 'Fall'
    END AS Season,
    YEAR(date) AS Year,
    MONTH(date) AS Month,
    pollutant_type,
    COUNT(DISTINCT location) AS LocationsMonitored,
    ROUND(AVG(avg_value), 2) AS AvgLevel,
    ROUND(STDEV(avg_value), 2) AS Volatility,
    COUNT(*) AS MeasurementDays
FROM gold_weather
GROUP BY YEAR(date), MONTH(date), pollutant_type
ORDER BY Year DESC, Month DESC, pollutant_type;

-- 5.3: Month-over-Month Growth/Decline
-- Shows if pollution is increasing or decreasing month-by-month
WITH MonthlyAvg AS (
    SELECT
        YEAR(date) AS Year,
        MONTH(date) AS Month,
        DATEFROMPARTS(YEAR(date), MONTH(date), 1) AS MonthStart,
        pollutant_type,
        ROUND(AVG(avg_value), 2) AS AvgLevel
    FROM gold_weather
    GROUP BY YEAR(date), MONTH(date), pollutant_type
)
SELECT
    Year,
    Month,
    MonthStart,
    pollutant_type,
    AvgLevel,
    LAG(AvgLevel) OVER (PARTITION BY pollutant_type ORDER BY Year, Month) AS PreviousMonthAvg,
    ROUND(
        AvgLevel - LAG(AvgLevel) OVER (PARTITION BY pollutant_type ORDER BY Year, Month),
        2
    ) AS AbsoluteChange,
    ROUND(
        (AvgLevel - LAG(AvgLevel) OVER (PARTITION BY pollutant_type ORDER BY Year, Month)) / 
        LAG(AvgLevel) OVER (PARTITION BY pollutant_type ORDER BY Year, Month) * 100,
        2
    ) AS PercentChange
FROM MonthlyAvg
ORDER BY Year DESC, Month DESC, pollutant_type;

-- ============================================================================
-- 6. COMPLIANCE & REGULATORY ANALYSIS
-- ============================================================================

-- 6.1: Days Exceeding Limits
-- Counts how many days each location exceeded pollutant limits
SELECT
    location,
    zone,
    pollutant_type,
    SUM(CASE WHEN (pollutant_type = 'PM2.5' AND avg_value > 35.4) 
             OR (pollutant_type = 'NO2' AND avg_value > 200) THEN 1 ELSE 0 END) AS UnhealthyDays,
    SUM(CASE WHEN (pollutant_type = 'PM2.5' AND avg_value BETWEEN 12 AND 35.4) 
             OR (pollutant_type = 'NO2' AND avg_value BETWEEN 100 AND 200) THEN 1 ELSE 0 END) AS ModerateDays,
    COUNT(DISTINCT date) AS TotalDaysTracked,
    ROUND(
        100.0 * SUM(CASE WHEN (pollutant_type = 'PM2.5' AND avg_value > 35.4) 
                         OR (pollutant_type = 'NO2' AND avg_value > 200) THEN 1 ELSE 0 END) / 
        COUNT(DISTINCT date),
        2
    ) AS ExceedancePercent
FROM gold_weather
WHERE date >= DATEADD(DAY, -90, CAST(GETDATE() AS DATE))
GROUP BY location, zone, pollutant_type
ORDER BY ExceedancePercent DESC;

-- 6.2: Regulatory Compliance Status
-- Overall compliance summary for reporting
SELECT
    CAST(GETDATE() AS DATE) AS ReportDate,
    COUNT(DISTINCT location) AS LocationsMonitored,
    COUNT(DISTINCT date) AS DataDays,
    ROUND(100.0 * SUM(CASE WHEN avg_value <= 35.4 THEN 1 ELSE 0 END) / COUNT(*), 2) AS ComplianceRate,
    SUM(CASE WHEN (pollutant_type = 'PM2.5' AND avg_value > 35.4) 
             OR (pollutant_type = 'NO2' AND avg_value > 200) THEN 1 ELSE 0 END) AS ViolationDays,
    CASE
        WHEN ROUND(100.0 * SUM(CASE WHEN avg_value <= 35.4 THEN 1 ELSE 0 END) / COUNT(*), 2) >= 95 THEN 'COMPLIANT'
        WHEN ROUND(100.0 * SUM(CASE WHEN avg_value <= 35.4 THEN 1 ELSE 0 END) / COUNT(*), 2) >= 85 THEN 'MOSTLY COMPLIANT'
        ELSE 'NON-COMPLIANT'
    END AS ComplianceStatus
FROM gold_weather
WHERE date >= DATEADD(DAY, -90, CAST(GETDATE() AS DATE));

-- ============================================================================
-- 7. PREDICTIVE & FORECASTING PREP
-- ============================================================================

-- 7.1: Data Volatility (for forecast confidence)
-- Shows measurement stability - high volatility = harder to forecast
SELECT
    location,
    pollutant_type,
    ROUND(AVG(avg_value), 2) AS MeanValue,
    ROUND(STDEV(avg_value), 2) AS StdDev,
    ROUND(STDEV(avg_value) / NULLIF(AVG(avg_value), 0), 2) AS CoefficientOfVariation,
    CASE
        WHEN STDEV(avg_value) / NULLIF(AVG(avg_value), 0) < 0.15 THEN 'STABLE'
        WHEN STDEV(avg_value) / NULLIF(AVG(avg_value), 0) < 0.30 THEN 'MODERATE'
        ELSE 'VOLATILE'
    END AS VolatilityLevel,
    COUNT(DISTINCT date) AS DataPoints
FROM gold_weather
WHERE date >= DATEADD(DAY, -90, CAST(GETDATE() AS DATE))
GROUP BY location, pollutant_type
ORDER BY CoefficientOfVariation DESC;

-- 7.2: Trend Direction (Simple Linear Trend)
-- Calculates if pollution is trending up or down
WITH RankedData AS (
    SELECT
        location,
        pollutant_type,
        date,
        avg_value,
        ROW_NUMBER() OVER (PARTITION BY location, pollutant_type ORDER BY date) AS DayNumber
    FROM gold_weather
    WHERE date >= DATEADD(DAY, -90, CAST(GETDATE() AS DATE))
)
SELECT
    location,
    pollutant_type,
    COUNT(*) AS DataPoints,
    ROUND(AVG(avg_value), 2) AS AvgValue,
    ROUND(
        (SUM(DayNumber * avg_value) - COUNT(*) * AVG(DayNumber) * AVG(avg_value)) / 
        (SUM(DayNumber * DayNumber) - COUNT(*) * AVG(DayNumber) * AVG(DayNumber)),
        4
    ) AS TrendSlope,
    CASE
        WHEN (SUM(DayNumber * avg_value) - COUNT(*) * AVG(DayNumber) * AVG(avg_value)) / 
             (SUM(DayNumber * DayNumber) - COUNT(*) * AVG(DayNumber) * AVG(DayNumber)) > 0.01 THEN 'INCREASING'
        WHEN (SUM(DayNumber * avg_value) - COUNT(*) * AVG(DayNumber) * AVG(avg_value)) / 
             (SUM(DayNumber * DayNumber) - COUNT(*) * AVG(DayNumber) * AVG(DayNumber)) < -0.01 THEN 'DECREASING'
        ELSE 'STABLE'
    END AS TrendDirection
FROM RankedData
GROUP BY location, pollutant_type
ORDER BY ABS(TrendSlope) DESC;

-- ============================================================================
-- 8. EXECUTIVE SUMMARY DASHBOARD
-- ============================================================================

-- 8.1: Key Metrics Summary
-- One query for executive dashboard
SELECT
    'Overall Health' AS Metric,
    CASE
        WHEN (SELECT ROUND(100.0 * COUNT(*) FILTER (WHERE avg_value <= 35) / COUNT(*), 2)
              FROM gold_weather
              WHERE date >= DATEADD(DAY, -30, CAST(GETDATE() AS DATE))) > 85 THEN 'GOOD'
        ELSE 'NEEDS ATTENTION'
    END AS Status,
    (SELECT ROUND(100.0 * COUNT(*) FILTER (WHERE avg_value <= 35) / COUNT(*), 2)
     FROM gold_weather
     WHERE date >= DATEADD(DAY, -30, CAST(GETDATE() AS DATE))) AS Percentage
UNION ALL
SELECT
    'Highest Risk Location',
    (SELECT TOP 1 location FROM gold_weather WHERE date >= DATEADD(DAY, -30, CAST(GETDATE() AS DATE))
     GROUP BY location ORDER BY AVG(avg_value) DESC),
    (SELECT TOP 1 ROUND(AVG(avg_value), 2) FROM gold_weather WHERE date >= DATEADD(DAY, -30, CAST(GETDATE() AS DATE))
     GROUP BY location ORDER BY AVG(avg_value) DESC)
UNION ALL
SELECT
    'Days Over Limit (Last 30d)',
    CAST((SELECT COUNT(DISTINCT date) FROM gold_weather 
          WHERE date >= DATEADD(DAY, -30, CAST(GETDATE() AS DATE))
          AND avg_value > 35.4) AS VARCHAR),
    NULL;

-- ============================================================================
-- STORED PROCEDURE: Generate Monthly Report
-- ============================================================================

-- 8.2: Monthly Compliance Report
-- Can be scheduled to run automatically
SELECT
    DATEFROMPARTS(YEAR(date), MONTH(date), 1) AS ReportMonth,
    COUNT(DISTINCT location) AS MonitoringLocations,
    COUNT(DISTINCT date) AS DaysOfData,
    ROUND(AVG(avg_value), 2) AS AvgPollutionLevel,
    MAX(max_value) AS PeakLevel,
    SUM(CASE WHEN avg_value > 35.4 THEN 1 ELSE 0 END) AS ExceedanceDays,
    ROUND(100.0 * SUM(CASE WHEN avg_value > 35.4 THEN 1 ELSE 0 END) / COUNT(*), 2) AS ExceedanceRate,
    COUNT(DISTINCT pollutant_type) AS PollutantsTracked
FROM gold_weather
GROUP BY YEAR(date), MONTH(date)
ORDER BY YEAR(date) DESC, MONTH(date) DESC;

-- ============================================================================
-- NOTES FOR SYNAPSE USERS
-- ============================================================================

/*
EXECUTION TIPS:

1. WORKSPACE SETUP (if not already done):
   - Ensure you have a Synapse SQL Pool (Dedicated) or use Serverless SQL
   - Create external table pointing to gold layer parquet files in ADLS

2. CREATE EXTERNAL TABLE (Example):
   CREATE EXTERNAL TABLE [gold_weather]
   (
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
       LOCATION = 'gold/weather/*.parquet',
       DATA_SOURCE = ds_datalake,
       FILE_FORMAT = ff_parquet
   )

3. PERFORMANCE NOTES:
   - Pre-aggregate if possible for large datasets
   - Use DATEADD() to limit date ranges
   - Consider materialized views for frequent queries
   - Use Dedicated Pool for complex queries, Serverless for ad-hoc

4. SCHEDULING:
   - Use Data Factory to schedule these reports
   - Export results to Power BI for visualization
   - Set up alerts on key thresholds

5. CUSTOMIZATION:
   - Adjust WHO guidelines/thresholds based on your requirements
   - Add more pollutant types as data becomes available
   - Include weather data (temperature, wind) if available
*/

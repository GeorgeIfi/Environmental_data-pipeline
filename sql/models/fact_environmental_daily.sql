CREATE TABLE fact_air_quality_daily AS
SELECT 
    date,
    location,
    pollutant_type,
    value,
    unit,
    status
FROM {{ ref('raw_data') }}
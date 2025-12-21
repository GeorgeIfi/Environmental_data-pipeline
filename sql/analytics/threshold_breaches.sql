SELECT 
    date,
    location,
    pollutant_type,
    value
FROM fact_air_quality_daily
WHERE value > 5.0  -- WHO air quality threshold
ORDER BY value DESC
SELECT 
    date,
    AVG(value) as avg_pollution,
    MAX(value) as max_pollution
FROM fact_air_quality_daily
GROUP BY date
ORDER BY date
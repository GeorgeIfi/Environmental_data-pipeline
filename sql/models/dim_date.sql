CREATE TABLE dim_date AS
SELECT DISTINCT
    date,
    EXTRACT(year FROM date) as year,
    EXTRACT(month FROM date) as month,
    EXTRACT(day FROM date) as day
FROM {{ ref('raw_data') }}
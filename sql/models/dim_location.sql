CREATE TABLE dim_location AS
SELECT DISTINCT
    location,
    ROW_NUMBER() OVER (ORDER BY location) as location_id
FROM {{ ref('raw_data') }}
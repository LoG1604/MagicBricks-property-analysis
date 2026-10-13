-- queries.sql
-- Analysis questions for the MagicBricks project.
-- Sale analysis excludes price outliers. Run with: python src/run_queries.py

-- Q1 Which cities are the most expensive for buying (median price per sqft)?
SELECT
    city,
    COUNT(*) AS listings,
    ROUND(MEDIAN(price_per_sqft)) AS median_price_per_sqft,
    ROUND(MEDIAN(price_lakh), 1) AS median_price_lakh
FROM listings
WHERE transaction_type = 'Sale' AND NOT is_price_outlier
GROUP BY city
ORDER BY median_price_per_sqft DESC;

-- Q2 Which localities are the most expensive (at least 5 listings)?
SELECT
    city,
    locality,
    COUNT(*) AS listings,
    ROUND(MEDIAN(price_per_sqft)) AS median_price_per_sqft
FROM listings
WHERE transaction_type = 'Sale'
  AND NOT is_price_outlier
  AND locality <> 'Unknown'
GROUP BY city, locality
HAVING COUNT(*) >= 5
ORDER BY median_price_per_sqft DESC
LIMIT 10;

-- Q3 How does price per sqft change with BHK?
SELECT
    bhk,
    COUNT(*) AS listings,
    ROUND(MEDIAN(price_per_sqft)) AS median_price_per_sqft,
    ROUND(MEDIAN(area_sqft)) AS median_area_sqft
FROM listings
WHERE transaction_type = 'Sale' AND NOT is_price_outlier AND bhk IS NOT NULL
GROUP BY bhk
ORDER BY bhk;

-- Q4 Does a ready property cost more than one under construction?
SELECT
    property_status,
    COUNT(*) AS listings,
    ROUND(MEDIAN(price_per_sqft)) AS median_price_per_sqft,
    ROUND(MEDIAN(price_lakh), 1) AS median_price_lakh
FROM listings
WHERE transaction_type = 'Sale' AND NOT is_price_outlier
GROUP BY property_status
ORDER BY median_price_per_sqft DESC;

-- Q5 Does distance from the city center affect price?
SELECT
    CASE
        WHEN distance_from_city_center_km < 5 THEN '0-5 km'
        WHEN distance_from_city_center_km < 10 THEN '5-10 km'
        WHEN distance_from_city_center_km < 15 THEN '10-15 km'
        WHEN distance_from_city_center_km < 20 THEN '15-20 km'
        ELSE '20+ km'
    END AS distance_band,
    COUNT(*) AS listings,
    ROUND(MEDIAN(price_per_sqft)) AS median_price_per_sqft
FROM listings
WHERE transaction_type = 'Sale' AND NOT is_price_outlier
GROUP BY distance_band
ORDER BY MIN(distance_from_city_center_km);

-- Q6 How much does furnishing add to rent (rent per sqft)?
SELECT
    furnishing,
    COUNT(*) AS listings,
    ROUND(MEDIAN(price_per_sqft), 1) AS median_rent_per_sqft,
    ROUND(MEDIAN(monthly_rent)) AS median_monthly_rent
FROM listings
WHERE transaction_type = 'Rent' AND NOT is_price_outlier
GROUP BY furnishing
ORDER BY median_rent_per_sqft DESC;

-- Q7 Do amenities carry a price premium? (difference vs overall median)
WITH base AS (
    SELECT property_id, price_per_sqft
    FROM listings
    WHERE transaction_type = 'Sale' AND NOT is_price_outlier
)
SELECT
    a.amenity,
    COUNT(*) AS listings,
    ROUND(MEDIAN(b.price_per_sqft)) AS median_price_per_sqft,
    ROUND(MEDIAN(b.price_per_sqft) - (SELECT MEDIAN(price_per_sqft) FROM base)) AS vs_overall
FROM amenities a
JOIN base b ON a.property_id = b.property_id
GROUP BY a.amenity
ORDER BY vs_overall DESC;

-- Q8 Who posts the listings and how do their prices compare?
SELECT
    posted_by,
    COUNT(*) AS listings,
    ROUND(MEDIAN(price_per_sqft)) AS median_price_per_sqft
FROM listings
WHERE transaction_type = 'Sale' AND NOT is_price_outlier
GROUP BY posted_by
ORDER BY listings DESC;

-- Q9 How many listings were posted each month?
SELECT
    posted_month,
    COUNT(*) AS listings
FROM listings
GROUP BY posted_month
ORDER BY posted_month;
-- 7. Calculate Mean Price per meter at every district in HCM
SELECT district, AVG(price / area) "Mean price per meter squared" 
FROM houses 
GROUP BY city_province, district
HAVING city_province = 'Hồ Chí Minh'
ORDER BY "Mean price per meter squared" DESC;

-- 8. What is the average price for properties in District 1
SELECT AVG(price) "Average price at District 1" 
FROM houses 
WHERE city_province = 'Hồ Chí Minh' AND district = 'Quận 1'

-- 9. List all properties ordered by price from highest to lowest
SELECT * FROM houses ORDER BY price DESC;

-- 10. Mean price for each number of bedroom
SELECT n_bedrooms "Number of bedrooms", AVG(price) "Mean price" 
FROM houses 
GROUP BY n_bedrooms
ORDER BY n_bedrooms

-- 11. Find duplicated data
SELECT COUNT(*) AS DuplicateCount, *
FROM houses
GROUP BY
    price, area, n_bedrooms, n_bathrooms, property_type, address, legal_docs,
    city_province, facing_direction, front_width, district
HAVING DuplicateCount > 1;

-- 12. Descriptive statistics for every column
WITH quartiles AS (
    SELECT
        NTILE(4) OVER (ORDER BY price) quartiles,
        price
    FROM houses
)
SELECT
    -- MEAN (Average)
    AVG(Price) AS mean,

    -- STDEV (Standard Deviation)
    STDEV(Price) AS std_dev,

    -- Quartiles (25%, 50% - Median, 75%) using the PERCENTILE_CONT function (SQL Server 2012+)
    -- Note: PERCENTILE_CONT is an analytic function and requires an OVER clause
    (SELECT Max(price) from quartiles where quartiles = 1) lower_quartile,
    (SELECT Max(price) from quartiles where quartiles = 2) median,
    (SELECT Max(price) from quartiles where quartiles = 3) upper_quartile,
    -- Query to find the MODE of the Price
    (
        SELECT TOP 1 price,
        FROM houses
        GROUP BY price
        ORDER BY count(price) DESC;
    ) AS Mode
FROM
    houses;
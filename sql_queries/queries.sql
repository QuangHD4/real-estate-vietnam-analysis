-- Schema: TABLE houses (
    -- price TEXT, 
    -- area TEXT, 
    -- n_bedrooms TEXT, 
    -- n_bathrooms TEXT, 
    -- legal TEXT, 
    -- interior TEXT, 
    -- facing_direction TEXT, 
    -- balcony_direction TEXT, 
    -- front_width TEXT, 
    -- front_road_width TEXT, 
    -- title TEXT, 
    -- description TEXT, 
    -- latitude FLOAT, 
    -- longitude FLOAT, 
    -- verified SMALLINT, 
    -- location TEXT, 
    -- location_details TEXT, 
    -- property_type TEXT, 
    -- date_of_posting TEXT
-- );

--Q1: total number of properties
SELECT count(*) total_properties FROM houses ;

------------------------------------------------------------------------------------
--Q2: number of properties and avg price  by city_province
SELECT city_province, count(*) number_of_properties, AVG(price) AS average_price
FROM houses 
GROUP BY city_province;

------------------------------------------------------------------------------------
--Q3: number of properties, avg price, and price/m^2 by property_type
SELECT 
    property_type, 
    count(*) number_of_properties, 
    AVG(price) AS avg_price,
    AVG(price/NULLIF(area,0)) AS avg_price_per_m2
FROM houses 
GROUP BY property_type;

------------------------------------------------------------------------------------
--Q4: number of properties, avg price, and price/m^2 by legal documents available
SELECT 
    legal_docs, 
    count(*) number_of_properties, 
    AVG(price) AS avg_price,
    AVG(price/NULLIF(area,0)) AS avg_price_per_m2
FROM houses 
GROUP BY legal_docs;

------------------------------------------------------------------------------------
--Q5. avg price/m^2 vs. n_bedrooms: Does higher n_bedrooms correlate with higher density price?
select AVG(price/area) AvgPrice, n_bedrooms
from houses
group by n_bedrooms;

------------------------------------------------------------------------------------
--Q6: avg price/m^2 vs. property type & legal_docs
select AVG(price/area) AvgPrice, property_type, legal_docs
from houses
group by property_type, legal_docs;

------------------------------------------------------------------------------------
--Q7: number of properties with price under 5 billion
SELECT count(*) AS count_under_5_billion
FROM houses
WHERE price < 5000000000;

------------------------------------------------------------------------------------
--Q8: Mean of the price, area, price/m^2 in the top 10 district highest in price
SELECT district,AVG(price),AVG(area),AVG(price/NULLIF(area,0)) AS Average_price_per_m2
FROM houses
GROUP BY district
ORDER BY AVG(price) desc,AVG(area) desc
LIMIT 10

------------------------------------------------------------------------------------
--Q9: Categorize properties based on price ranges
SELECT
  CASE WHEN price<10 THEN '<10'     -- relatively affordable
    WHEN price<100 THEN '<100'      -- mid-upper segment
    ELSE '>=100'                    -- luxury segment/outliers
  END AS price_group,
  COUNT(*) AS Number,
  AVG(price) AS Average_price,
  AVG(price/NULLIF(area,0)) AS Average_price_per_m2
FROM houses
GROUP BY price_group

------------------------------------------------------------------------------------
--Q10: Set price vs. Negotiable price (on avg price, avg price/m^2, avg area, avg rooms)
with is_negotiable AS (
  select 
  	id,
  	CASE 
  	  WHEN price is not NULL then 0
  	  ELSE 1
  	END as is_negotiable
  FROM houses
)
select 
  is_negotiable, AVG(price/area) AvgPrice, AVG(area), AVG(n_bedrooms), AVG(n_bathrooms)
from 
  houses JOIN is_negotiable on houses.id = is_negotiable.id
group by is_negotiable;

------------------------------------------------------------------------------------
--Q11: Are certain property types more common in specific cities or districts?
select city_province, property_type, count(*) frequency
from houses
group by city_province, property_type
ORDER by city_province, frequency DESC;

------------------------------------------------------------------------------------
--Q12: correlation between price and area (easier done in python/R, but try in SQL)
SELECT 
    (
        (COUNT(*) * SUM(price * area)) - (SUM(price) * SUM(area))
    ) /
    (
        SQRT(
            (COUNT(*) * SUM(price * price) - (SUM(price) * SUM(price))) *
            (COUNT(*) * SUM(area * area) - (SUM(area) * SUM(area)))
        )
    ) AS correlation_price_area
FROM houses
WHERE price IS NOT NULL AND area IS NOT NULL;

------------------------------------------------------------------------------------
--Q13: find full records with no missing values, group by city_province (easier done in python/R, but try in SQL)
SELECT
  city_province,
  SUM(
    CASE WHEN price IS NOT NULL
      AND area IS NOT NULL
      AND n_bedrooms IS NOT NULL
      AND n_bathrooms IS NOT NULL
      AND property_type IS NOT NULL
      AND address IS NOT NULL
      AND legal_docs IS NOT NULL
      THEN 1 ELSE 0 END
  ) AS So_nha_dat_chuan,
  COUNT(*) AS Tong_so_nha,
  ROUND(
    1.0 * SUM(
      CASE WHEN price IS NOT NULL
        AND area IS NOT NULL
        AND n_bedrooms IS NOT NULL
        AND n_bathrooms IS NOT NULL
        AND property_type IS NOT NULL
        AND address IS NOT NULL
        AND legal_docs IS NOT NULL
        THEN 1 ELSE 0 END
    ) * 100 / COUNT(*),
  2) AS Percentage
FROM houses
GROUP BY city_province;
TOP_PRICE_QUERY = """
SELECT 
    article_id,
    SUM(price) AS total_sales
FROM transactions
WHERE article_id IN ({0})
GROUP BY article_id
ORDER BY total_sales DESC
LIMIT 1;
"""

PREV_MONTH_QUERY = """
WITH RECURSIVE months AS (
    -- Start from 2018-08-01
    SELECT DATE('2018-08-01') AS month
    UNION ALL
    -- Keep adding months until 2020-10-01
    SELECT DATE_ADD(month, INTERVAL 1 MONTH)
    FROM months
    WHERE month < DATE('2020-10-01')
),
monthly_sales AS (
    SELECT 
        DATE_FORMAT(t_dat, '%Y-%m-01') AS month,
        SUM(price) AS total_sales
    FROM transactions
    WHERE article_id = {0}
      AND t_dat >= '2018-08-01'
      AND t_dat <  '2020-11-01'   -- include October 2020
    GROUP BY DATE_FORMAT(t_dat, '%Y-%m-01')
)
SELECT 
    m.month,
    SUM(COALESCE(ms.total_sales, 0)) 
        OVER (ORDER BY m.month ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS cumulative_sales
FROM months m
LEFT JOIN monthly_sales ms 
       ON m.month = ms.month
ORDER BY m.month;
"""

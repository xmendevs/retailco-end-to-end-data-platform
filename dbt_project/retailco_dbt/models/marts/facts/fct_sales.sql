{{ config(
    materialized='table'
) }}

WITH raw_sales AS (
    SELECT * FROM {{ ref('stg_order_items') }}
),

-- Deduplicate order line items based on the latest update timestamp
deduped_sales AS (
    SELECT 
        *,
        ROW_NUMBER() OVER (
            PARTITION BY order_item_id 
            ORDER BY updated_at DESC
        ) as rn
    FROM raw_sales
)

SELECT 
    -- Generate your fact table surrogate key
    md5(cast(coalesce(cast(s.order_item_id as varchar), '') as varchar)) AS sales_key,
    s.order_item_id,
    s.order_id,
    
    -- Conformed dimension surrogate keys
    dc.customer_key,
    dp.product_key,
    ds.store_key,
    de.employee_key,
    
    -- Timestamps & Measures
    s.created_at,
    s.updated_at,
    s.quantity,
    s.unit_price AS price, -- 👈 Maps the actual source column name to standard 'price'
    (s.quantity * s.unit_price) AS gross_revenue -- 👈 Corrected mathematical multiplier
FROM deduped_sales s
LEFT JOIN {{ ref('stg_orders') }} o 
    ON s.order_id = o.order_id
LEFT JOIN {{ ref('dim_customers') }} dc 
    ON o.customer_id = dc.customer_id AND dc.is_current = TRUE
LEFT JOIN {{ ref('dim_products') }} dp 
    ON s.product_id = dp.product_id AND dp.is_current = TRUE
LEFT JOIN {{ ref('dim_stores') }} ds 
    ON o.store_id = ds.store_id
LEFT JOIN {{ ref('dim_employees') }} de 
    ON o.employee_id = de.employee_id
WHERE s.rn = 1
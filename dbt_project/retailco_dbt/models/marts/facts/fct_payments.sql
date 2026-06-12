{{ config(
    materialized='table'
) }}

WITH raw_payments AS (
    SELECT * FROM {{ ref('stg_payments') }}
),

-- Deduplicate payment records based on late arriving status changes
deduped_payments AS (
    SELECT 
        *,
        ROW_NUMBER() OVER (
            PARTITION BY payment_id 
            ORDER BY updated_at DESC
        ) as rn
    FROM raw_payments
)

SELECT
    p.payment_id,
    p.order_id,
    dc.customer_key,
    ds.store_key,
    dpm.payment_method_key,
    p.paid_at,
    p.created_at,
    p.updated_at,
    p.amount_paid
FROM deduped_payments p
LEFT JOIN {{ ref('stg_orders') }} o
    ON p.order_id = o.order_id
LEFT JOIN {{ ref('dim_customers') }} dc
    ON o.customer_id = dc.customer_id AND dc.is_current = TRUE
LEFT JOIN {{ ref('dim_stores') }} ds
    ON o.store_id = ds.store_id
LEFT JOIN {{ ref('dim_payment_method') }} dpm
    ON p.payment_method_id = dpm.payment_method_id
WHERE p.rn = 1 
  AND p.amount_paid > 0  -- Filters out anomalies as required by your data quality brief
WITH source AS (


SELECT *
FROM {{ source('raw', 'order_items') }}


)

SELECT


id::TEXT                 AS order_item_id,
team_id::TEXT            AS team_id,

order_id::TEXT           AS order_id,
product_id::TEXT         AS product_id,

quantity::INT            AS quantity,

unit_price::NUMERIC(12,2) AS unit_price,

discount_pct::NUMERIC(8,2) AS discount_pct,

line_total::NUMERIC(12,2) AS line_total,

created_at::TIMESTAMP AS created_at,
updated_at::TIMESTAMP AS updated_at


FROM source

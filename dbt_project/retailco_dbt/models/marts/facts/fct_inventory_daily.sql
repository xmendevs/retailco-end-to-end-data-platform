SELECT

DATE(moved_at) AS inventory_date,

product_id,
store_id,

SUM(quantity) AS net_quantity_moved,

COUNT(*) AS movement_count

FROM {{ source('raw', 'inventory_movements') }}

GROUP BY

DATE(moved_at),
product_id,
store_id

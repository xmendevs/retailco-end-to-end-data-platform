WITH source AS (


SELECT *
FROM {{ source('raw', 'products') }}

)

SELECT


id::TEXT                AS product_id,
team_id::TEXT           AS team_id,

sku::TEXT               AS sku,
name::TEXT              AS product_name,

category::TEXT          AS category,
sub_category::TEXT      AS sub_category,

brand::TEXT             AS brand,
supplier::TEXT          AS supplier,

cost_price::NUMERIC(12,2)    AS cost_price,
selling_price::NUMERIC(12,2) AS selling_price,

effective_from::TIMESTAMP AS effective_from,

is_deleted::BOOLEAN     AS is_deleted,

created_at::TIMESTAMP   AS created_at,
updated_at::TIMESTAMP   AS updated_at

FROM source


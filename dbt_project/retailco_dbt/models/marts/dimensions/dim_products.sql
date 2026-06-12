SELECT

{{ generate_surrogate_key([
    'product_id',
    'dbt_valid_from'
]) }} AS product_key,

product_id,
team_id,

sku,
product_name,

category,
sub_category,

brand,
supplier,

cost_price,
selling_price,

dbt_valid_from AS valid_from,
dbt_valid_to AS valid_to,

CASE
    WHEN dbt_valid_to IS NULL THEN TRUE
    ELSE FALSE
END AS is_current

FROM {{ ref('product_snapshot') }}
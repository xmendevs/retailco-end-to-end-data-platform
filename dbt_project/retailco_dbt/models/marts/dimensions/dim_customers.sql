SELECT

{{ generate_surrogate_key([
    'customer_id',
    'dbt_valid_from'
]) }} AS customer_key,

customer_id,
team_id,

first_name,
last_name,
full_name,

email,
phone,

segment,
tier,

address,
city,
state,

registered_at,
effective_from,

dbt_valid_from AS valid_from,
dbt_valid_to AS valid_to,

CASE
    WHEN dbt_valid_to IS NULL THEN TRUE
    ELSE FALSE
END AS is_current

FROM {{ ref('customer_snapshot') }}
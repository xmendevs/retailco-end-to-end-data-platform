SELECT

{{ generate_surrogate_key([
    'store_id'
]) }} AS store_key,

store_id,
team_id,

store_name,
city,
state,
address,
phone,
manager_name,
opened_date,

created_at,
updated_at

FROM {{ ref('stg_stores') }}
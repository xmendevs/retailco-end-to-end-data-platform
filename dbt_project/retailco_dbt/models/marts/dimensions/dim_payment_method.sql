SELECT

{{ generate_surrogate_key([
    'payment_method_id'
]) }} AS payment_method_key,

payment_method_id,
team_id,

method_name,
provider,
is_digital,

created_at,
updated_at

FROM {{ ref('stg_payment_methods') }}


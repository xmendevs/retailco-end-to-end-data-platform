WITH source AS (


SELECT *
FROM {{ source('raw', 'payments') }}


)

SELECT


id::TEXT                     AS payment_id,
team_id::TEXT                AS team_id,

order_id::TEXT               AS order_id,
customer_id::TEXT            AS customer_id,

payment_method_id::TEXT      AS payment_method_id,

amount_paid::NUMERIC(12,2)   AS amount_paid,

currency::TEXT               AS currency,
status::TEXT                 AS status,

payment_type::TEXT           AS payment_type,

reference::TEXT              AS reference,

paid_at::TIMESTAMP           AS paid_at,

created_at::TIMESTAMP        AS created_at,
updated_at::TIMESTAMP        AS updated_at

FROM source

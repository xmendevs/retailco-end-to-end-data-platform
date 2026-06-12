WITH source AS (


SELECT *
FROM {{ source('raw', 'orders') }}


)

SELECT


id::TEXT                    AS order_id,
team_id::TEXT               AS team_id,

customer_id::TEXT           AS customer_id,
store_id::TEXT              AS store_id,
employee_id::TEXT           AS employee_id,

status::TEXT                AS status,

discount_code::TEXT         AS discount_code,
discount_amount::NUMERIC(12,2) AS discount_amount,

total_amount::NUMERIC(12,2) AS total_amount,

ordered_at::TIMESTAMP       AS ordered_at,
paid_at::TIMESTAMP          AS paid_at,
shipped_at::TIMESTAMP       AS shipped_at,
delivered_at::TIMESTAMP     AS delivered_at,
cancelled_at::TIMESTAMP     AS cancelled_at,

created_at::TIMESTAMP       AS created_at,
updated_at::TIMESTAMP       AS updated_at


FROM source


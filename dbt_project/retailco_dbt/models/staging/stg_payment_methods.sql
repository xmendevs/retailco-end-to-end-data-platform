WITH source AS (


SELECT *
FROM {{ source('raw', 'payment_methods') }}


)

SELECT


id::TEXT              AS payment_method_id,
team_id::TEXT         AS team_id,

name::TEXT            AS method_name,

provider::TEXT        AS provider,

is_digital::BOOLEAN   AS is_digital,

created_at::TIMESTAMP AS created_at,
updated_at::TIMESTAMP AS updated_at


FROM source


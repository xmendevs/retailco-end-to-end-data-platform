WITH source AS (


SELECT *
FROM {{ source('raw', 'employees') }}


)

SELECT


id::TEXT               AS employee_id,
team_id::TEXT          AS team_id,

store_id::TEXT         AS store_id,

first_name::TEXT       AS first_name,
last_name::TEXT        AS last_name,

CONCAT(first_name,' ',last_name)
                        AS full_name,

email::TEXT            AS email,

role::TEXT             AS role,

hired_date::DATE       AS hired_date,

is_deleted::BOOLEAN    AS is_deleted,

created_at::TIMESTAMP  AS created_at,
updated_at::TIMESTAMP  AS updated_at

FROM source

WITH source AS (

SELECT *
FROM {{ source('raw', 'stores') }}

)

SELECT

id::TEXT                  AS store_id,
team_id::TEXT             AS team_id,

name::TEXT                AS store_name,

city::TEXT                AS city,
state::TEXT               AS state,

address::TEXT             AS address,
phone::TEXT               AS phone,

manager_name::TEXT        AS manager_name,

opened_date::DATE         AS opened_date,

created_at::TIMESTAMP     AS created_at,
updated_at::TIMESTAMP     AS updated_at

FROM source


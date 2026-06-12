WITH source AS (

    SELECT *
    FROM {{ source('raw', 'customers') }}

)

SELECT
    id::TEXT                  AS customer_id,
    team_id::TEXT             AS team_id,

    first_name::TEXT          AS first_name,
    last_name::TEXT           AS last_name,

    CONCAT(first_name,' ',last_name) AS full_name,

    email::TEXT               AS email,
    
    REPLACE(REPLACE(phone, '/', ''), '-', '')::TEXT AS phone,

    segment::TEXT             AS segment,
    tier::TEXT                AS tier,

    address::TEXT             AS address,
    city::TEXT                AS city,
    state::TEXT               AS state,

    effective_from::TIMESTAMP AS effective_from,
    registered_at::TIMESTAMP  AS registered_at,

    is_deleted::BOOLEAN       AS is_deleted,

    created_at::TIMESTAMP     AS created_at,
    updated_at::TIMESTAMP     AS updated_at

FROM source
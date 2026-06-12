SELECT *

FROM {{ ref('stg_payments') }}

WHERE amount_paid <= 0
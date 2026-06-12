SELECT

order_id,

customer_id,
store_id,
employee_id,

ordered_at,
paid_at,
shipped_at,
delivered_at,

EXTRACT(
    EPOCH FROM (paid_at - ordered_at)
)/3600
AS hours_to_payment,

EXTRACT(
    EPOCH FROM (shipped_at - paid_at)
)/3600
AS hours_to_ship,

EXTRACT(
    EPOCH FROM (delivered_at - shipped_at)
)/3600
AS hours_to_delivery

FROM {{ ref('stg_orders') }}
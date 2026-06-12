WITH dates AS (

SELECT generate_series(
    '2024-01-01'::date,
    '2027-12-31'::date,
    interval '1 day'
)::date AS date_day

)

SELECT

TO_CHAR(date_day,'YYYYMMDD')::INT AS date_key,

date_day,

EXTRACT(YEAR FROM date_day) AS year,

EXTRACT(QUARTER FROM date_day) AS quarter,

EXTRACT(MONTH FROM date_day) AS month,

EXTRACT(WEEK FROM date_day) AS week,

TRIM(TO_CHAR(date_day,'Day')) AS day_of_week,

CASE
    WHEN EXTRACT(ISODOW FROM date_day) IN (6,7)
    THEN TRUE
    ELSE FALSE
END AS is_weekend

FROM dates
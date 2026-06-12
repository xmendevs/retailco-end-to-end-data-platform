SELECT

{{ generate_surrogate_key([
    'employee_id'
]) }} AS employee_key,

employee_id,
team_id,

first_name,
last_name,
email,

role,
hired_date,
is_deleted,

store_id,

created_at,
updated_at

FROM {{ ref('stg_employees') }}
with bounds as (
    select
        min((interval_start_utc at time zone 'UTC')::date) as first_day,
        max((interval_start_utc at time zone 'UTC')::date) as last_day
    from {{ ref('int_telecom__activity_latest') }}
), dates as (
    select generate_series(first_day::timestamp, last_day::timestamp, interval '1 day')::date as full_date
    from bounds
)

select
    to_char(full_date, 'YYYYMMDD')::integer as date_key,
    full_date,
    extract(year from full_date)::integer as year,
    extract(month from full_date)::integer as month,
    extract(isoyear from full_date)::integer as iso_year,
    extract(week from full_date)::integer as iso_week,
    extract(isodow from full_date)::integer as iso_weekday
from dates

-- A valid foreign key must point to the correct natural attributes, not just any dimension row.
with expected as (
    select
        *,
        {{ stable_key(['source_system', 'square_id', 'interval_start_ms', 'country_code']) }} as activity_key
    from {{ ref('int_telecom__activity_latest') }}
)
select f.activity_key
from {{ ref('fct_grid_activity') }} f
join expected e on f.activity_key = e.activity_key
join {{ ref('dim_grid') }} g on f.grid_key = g.grid_key
join {{ ref('dim_country') }} c on f.country_key = c.country_key
join {{ ref('dim_date') }} d on f.date_key = d.date_key
where g.source_system is distinct from e.source_system
   or g.square_id is distinct from e.square_id
   or c.country_code is distinct from e.country_code
   or d.full_date is distinct from (e.interval_start_utc at time zone 'UTC')::date
   or f.interval_start_ms is distinct from e.interval_start_ms
   or f.interval_start_utc is distinct from e.interval_start_utc

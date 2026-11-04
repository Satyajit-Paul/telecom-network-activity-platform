with countries as (
    select distinct country_code
    from {{ ref('int_telecom__activity_latest') }}
)
select
    {{ stable_key(['country_code']) }} as country_key,
    country_code
from countries

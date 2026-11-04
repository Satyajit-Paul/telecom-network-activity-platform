with grids as (
    select distinct source_system, square_id
    from {{ ref('int_telecom__activity_latest') }}
)
select
    {{ stable_key(['source_system', 'square_id']) }} as grid_key,
    source_system,
    square_id
from grids

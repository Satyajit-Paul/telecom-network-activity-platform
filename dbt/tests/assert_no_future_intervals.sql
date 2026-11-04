select activity_key
from {{ ref('fct_grid_activity') }}
where interval_start_utc > current_timestamp

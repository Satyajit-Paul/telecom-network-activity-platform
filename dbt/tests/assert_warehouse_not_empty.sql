select count(*) as row_count
from {{ ref('fct_grid_activity') }}
having count(*) = 0

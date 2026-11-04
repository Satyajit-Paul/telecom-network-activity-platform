with activity as (
    select * from {{ ref('int_telecom__activity_latest') }}
)
select
    {{ stable_key(['source_system', 'square_id', 'interval_start_ms', 'country_code']) }} as activity_key,
    {{ stable_key(['source_system', 'square_id']) }} as grid_key,
    {{ stable_key(['country_code']) }} as country_key,
    to_char(interval_start_utc at time zone 'UTC', 'YYYYMMDD')::integer as date_key,
    source_system,
    interval_start_ms,
    interval_start_utc,
    batch_id as source_batch_id,
    line_number as source_line_number,
    sms_in,
    sms_out,
    call_in,
    call_out,
    internet_activity
from activity

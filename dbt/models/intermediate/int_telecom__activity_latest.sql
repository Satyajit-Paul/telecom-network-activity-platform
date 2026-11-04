with staged as (
    select * from {{ ref('stg_telecom__activity') }}
), ranked as (
    select
        *,
        row_number() over (
            partition by source_system, square_id, interval_start_ms, country_code
            order by batch_id desc, line_number desc
        ) as row_rank
    from staged
)

select
    source_system, batch_id, line_number, ingested_at, square_id,
    interval_start_ms, interval_start_utc, country_code,
    sms_in, sms_out, call_in, call_out, internet_activity
from ranked
where row_rank = 1

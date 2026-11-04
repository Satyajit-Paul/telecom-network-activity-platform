-- Independently derive winning raw versions and verify fact coverage, lineage and values.
with latest_raw as (
    select distinct on (
        b.source_system, (r.source_fields ->> 0)::integer,
        (r.source_fields ->> 1)::bigint, r.source_fields ->> 2
    )
        b.source_system,
        r.batch_id,
        r.line_number,
        (r.source_fields ->> 0)::integer as square_id,
        (r.source_fields ->> 1)::bigint as interval_start_ms,
        r.source_fields ->> 2 as country_code,
        r.source_fields
    from {{ source('telecom_raw', 'activity_records') }} r
    join {{ source('telecom_raw', 'ingestion_batches') }} b on r.batch_id = b.batch_id
    where b.status = 'succeeded'
    order by b.source_system, (r.source_fields ->> 0)::integer,
        (r.source_fields ->> 1)::bigint, r.source_fields ->> 2,
        r.batch_id desc, r.line_number desc
), expected as (
    select *, {{ stable_key(['source_system', 'square_id', 'interval_start_ms', 'country_code']) }} as activity_key
    from latest_raw
), actual as (
    select * from {{ ref('fct_grid_activity') }}
)
select coalesce(expected.activity_key, actual.activity_key) as failing_activity_key
from expected
full outer join actual on expected.activity_key = actual.activity_key
where expected.activity_key is null
    or actual.activity_key is null
    or actual.source_batch_id is distinct from expected.batch_id
    or actual.source_line_number is distinct from expected.line_number
    or actual.source_system is distinct from expected.source_system
    or actual.sms_in is distinct from nullif(expected.source_fields ->> 3, '')::numeric
    or actual.sms_out is distinct from nullif(expected.source_fields ->> 4, '')::numeric
    or actual.call_in is distinct from nullif(expected.source_fields ->> 5, '')::numeric
    or actual.call_out is distinct from nullif(expected.source_fields ->> 6, '')::numeric
    or actual.internet_activity is distinct from nullif(expected.source_fields ->> 7, '')::numeric

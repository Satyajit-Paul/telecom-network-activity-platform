with raw_records as (
    select * from {{ source('telecom_raw', 'activity_records') }}
), batches as (
    select * from {{ source('telecom_raw', 'ingestion_batches') }}
)

select
    batches.source_system,
    raw_records.batch_id,
    raw_records.line_number,
    batches.ingested_at,
    (raw_records.source_fields ->> 0)::integer as square_id,
    (raw_records.source_fields ->> 1)::bigint as interval_start_ms,
    to_timestamp((raw_records.source_fields ->> 1)::numeric / 1000.0) as interval_start_utc,
    raw_records.source_fields ->> 2 as country_code,
    nullif(raw_records.source_fields ->> 3, '')::numeric as sms_in,
    nullif(raw_records.source_fields ->> 4, '')::numeric as sms_out,
    nullif(raw_records.source_fields ->> 5, '')::numeric as call_in,
    nullif(raw_records.source_fields ->> 6, '')::numeric as call_out,
    nullif(raw_records.source_fields ->> 7, '')::numeric as internet_activity
from raw_records
inner join batches on raw_records.batch_id = batches.batch_id
where batches.status = 'succeeded'

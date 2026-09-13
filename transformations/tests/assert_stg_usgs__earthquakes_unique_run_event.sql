select
    ingestion_run_id,
    event_id,
    count(*) as record_count
from {{ ref('stg_usgs__earthquakes') }}
group by
    ingestion_run_id,
    event_id
having count(*) > 1

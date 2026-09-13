with staged as (

    select *
    from {{ ref('stg_usgs__earthquakes') }}

),

ranked as (

    select
        *,
        row_number() over (
            partition by event_id
            order by
                updated_time desc,
                ingested_at desc,
                ingestion_run_id desc
        ) as event_version_rank

    from staged

),

latest as (

    select *
    from ranked
    where event_version_rank = 1

),

final as (

    select
        event_id,

        event_time,
        event_time::date as event_date,
        extract(hour from event_time)::integer as event_hour_utc,

        updated_time,

        magnitude,
        magnitude_type,

        case
            when magnitude < 2.0 then 'micro'
            when magnitude < 4.0 then 'minor'
            when magnitude < 5.0 then 'light'
            when magnitude < 6.0 then 'moderate'
            when magnitude < 7.0 then 'strong'
            when magnitude < 8.0 then 'major'
            else 'great'
        end as magnitude_class,

        place,

        longitude,
        latitude,
        depth_km,

        significance,
        tsunami = 1 as tsunami_flag,

        status,
        network,
        event_type,

        felt_reports,
        cdi,
        mmi,
        alert,

        ingestion_run_id as latest_ingestion_run_id,
        ingested_at as latest_ingested_at

    from latest

)

select *
from final

with source as (

    select *
    from {{ source('usgs', 'earthquakes') }}

),

renamed as (

    select
        ingestion_run_id,
        ingested_at,
        event_id,
        feature_type,
        geometry_type,

        longitude,
        latitude,
        depth_km,

        magnitude,
        magnitude_type,
        place,

        to_timestamp(event_time_epoch_ms / 1000.0) as event_time,
        to_timestamp(updated_time_epoch_ms / 1000.0) as updated_time,

        event_time_epoch_ms,
        updated_time_epoch_ms,
        timezone_offset,

        event_url,
        detail_url,

        felt_reports,
        cdi,
        mmi,
        alert,
        status,
        tsunami,
        significance,

        network,
        code,
        ids,
        sources,
        types,

        station_count,
        minimum_distance,
        rms,
        azimuthal_gap,

        event_type,
        title

    from source

)

select *
from renamed

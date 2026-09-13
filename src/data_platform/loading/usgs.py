from datetime import datetime
from typing import Any
from uuid import UUID

from azure.storage.blob import ContainerClient
from psycopg import Connection

from data_platform.ingestion.pipeline import count_geojson_features

INSERT_RAW_USGS_SQL = """
WITH source AS (
    SELECT %s::jsonb AS document
)
INSERT INTO raw.usgs_earthquakes (
    ingestion_run_id,
    ingested_at,
    event_id,
    feature_type,
    geometry_type,
    longitude,
    latitude,
    depth_km,
    magnitude,
    place,
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
    magnitude_type,
    event_type,
    title
)
SELECT
    %s,
    %s,
    feature->>'id',
    feature->>'type',
    feature->'geometry'->>'type',
    (feature->'geometry'->'coordinates'->>0)::double precision,
    (feature->'geometry'->'coordinates'->>1)::double precision,
    (feature->'geometry'->'coordinates'->>2)::double precision,
    (feature->'properties'->>'mag')::double precision,
    feature->'properties'->>'place',
    (feature->'properties'->>'time')::bigint,
    (feature->'properties'->>'updated')::bigint,
    (feature->'properties'->>'tz')::integer,
    feature->'properties'->>'url',
    feature->'properties'->>'detail',
    (feature->'properties'->>'felt')::integer,
    (feature->'properties'->>'cdi')::double precision,
    (feature->'properties'->>'mmi')::double precision,
    feature->'properties'->>'alert',
    feature->'properties'->>'status',
    (feature->'properties'->>'tsunami')::integer,
    (feature->'properties'->>'sig')::integer,
    feature->'properties'->>'net',
    feature->'properties'->>'code',
    feature->'properties'->>'ids',
    feature->'properties'->>'sources',
    feature->'properties'->>'types',
    (feature->'properties'->>'nst')::integer,
    (feature->'properties'->>'dmin')::double precision,
    (feature->'properties'->>'rms')::double precision,
    (feature->'properties'->>'gap')::double precision,
    feature->'properties'->>'magType',
    feature->'properties'->>'type',
    feature->'properties'->>'title'
FROM source
CROSS JOIN LATERAL
    jsonb_array_elements(source.document->'features') AS feature
ON CONFLICT (ingestion_run_id, event_id) DO NOTHING;
"""

COUNT_RAW_USGS_SQL = """
SELECT count(*)
FROM raw.usgs_earthquakes
WHERE ingestion_run_id = %s;
"""


def load_usgs_blob_to_raw(
    connection: Connection[Any],
    container: ContainerClient,
    *,
    run_id: UUID,
    blob_path: str,
    ingested_at: datetime,
) -> int:
    blob = container.get_blob_client(blob_path)
    payload = blob.download_blob().readall()

    expected_records = count_geojson_features(payload)
    payload_text = payload.decode("utf-8")

    with connection.cursor() as cursor:
        cursor.execute(
            INSERT_RAW_USGS_SQL,
            (
                payload_text,
                run_id,
                ingested_at,
            ),
        )

        cursor.execute(
            COUNT_RAW_USGS_SQL,
            (run_id,),
        )

        result = cursor.fetchone()

    if result is None:
        connection.rollback()
        raise RuntimeError("Could not validate raw USGS load")

    persisted_records = int(result[0])

    if persisted_records != expected_records:
        connection.rollback()
        raise RuntimeError(
            "Raw USGS load validation failed: "
            f"expected {expected_records} records, "
            f"found {persisted_records}"
        )

    connection.commit()

    return persisted_records

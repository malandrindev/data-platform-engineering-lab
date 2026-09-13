CREATE SCHEMA IF NOT EXISTS raw;

CREATE TABLE IF NOT EXISTS raw.usgs_earthquakes (
    ingestion_run_id uuid NOT NULL,
    ingested_at timestamptz NOT NULL,

    event_id text NOT NULL,
    feature_type text,

    geometry_type text,
    longitude double precision,
    latitude double precision,
    depth_km double precision,

    magnitude double precision,
    place text,
    event_time_epoch_ms bigint,
    updated_time_epoch_ms bigint,
    timezone_offset integer,
    event_url text,
    detail_url text,
    felt_reports integer,
    cdi double precision,
    mmi double precision,
    alert text,
    status text,
    tsunami integer,
    significance integer,
    network text,
    code text,
    ids text,
    sources text,
    types text,
    station_count integer,
    minimum_distance double precision,
    rms double precision,
    azimuthal_gap double precision,
    magnitude_type text,
    event_type text,
    title text,

    CONSTRAINT pk_raw_usgs_earthquakes
        PRIMARY KEY (ingestion_run_id, event_id),

    CONSTRAINT fk_raw_usgs_earthquakes_pipeline_run
        FOREIGN KEY (ingestion_run_id)
        REFERENCES pipeline_runs (run_id)
);

COMMENT ON TABLE raw.usgs_earthquakes IS
    'Raw relational representation of USGS earthquake GeoJSON features.';

COMMENT ON COLUMN raw.usgs_earthquakes.ingestion_run_id IS
    'Pipeline execution that produced the source snapshot.';

COMMENT ON COLUMN raw.usgs_earthquakes.event_time_epoch_ms IS
    'USGS event time preserved as Unix epoch milliseconds.';

COMMENT ON COLUMN raw.usgs_earthquakes.updated_time_epoch_ms IS
    'USGS update time preserved as Unix epoch milliseconds.';

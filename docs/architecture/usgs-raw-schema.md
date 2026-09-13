# USGS Raw Relational Schema

## Purpose

Define the relational representation of USGS earthquake GeoJSON features
loaded from immutable raw Blob snapshots into PostgreSQL.

Target relation:

`raw.usgs_earthquakes`

The relational raw layer remains close to the source representation and does
not contain analytical business logic.

## Grain

One row represents one USGS GeoJSON feature observed during one ingestion run.

The same earthquake event may appear in multiple ingestion runs because the
source can update event attributes after initial publication.

Therefore, `event_id` alone is not unique across the raw history.

Logical key:

`(ingestion_run_id, event_id)`

## Technical Metadata

| Column | PostgreSQL Type | Nullable | Description |
|---|---|---:|---|
| ingestion_run_id | uuid | no | Pipeline execution that produced the snapshot |
| ingested_at | timestamptz | no | Time the relational raw row was loaded |

`ingestion_run_id` should reference `pipeline_runs.run_id`.

## GeoJSON Feature Fields

| Source | Raw Column | PostgreSQL Type |
|---|---|---|
| feature.id | event_id | text |
| feature.type | feature_type | text |

Observed feature type:

`Feature`

## Geometry

All 213 records in the validated snapshot used GeoJSON `Point` geometry with
three coordinates.

GeoJSON coordinate order:

`[longitude, latitude, depth]`

| Source | Raw Column | PostgreSQL Type |
|---|---|---|
| geometry.type | geometry_type | text |
| geometry.coordinates[0] | longitude | double precision |
| geometry.coordinates[1] | latitude | double precision |
| geometry.coordinates[2] | depth_km | double precision |

No PostGIS dependency is required for the initial foundation.

Geospatial extensions can be introduced later if analytical requirements
justify them.

## USGS Properties

| Source Property | Raw Column | PostgreSQL Type |
|---|---|---|
| mag | magnitude | double precision |
| place | place | text |
| time | event_time_epoch_ms | bigint |
| updated | updated_time_epoch_ms | bigint |
| tz | timezone_offset | integer |
| url | event_url | text |
| detail | detail_url | text |
| felt | felt_reports | integer |
| cdi | cdi | double precision |
| mmi | mmi | double precision |
| alert | alert | text |
| status | status | text |
| tsunami | tsunami | integer |
| sig | significance | integer |
| net | network | text |
| code | code | text |
| ids | ids | text |
| sources | sources | text |
| types | types | text |
| nst | station_count | integer |
| dmin | minimum_distance | double precision |
| rms | rms | double precision |
| gap | azimuthal_gap | double precision |
| magType | magnitude_type | text |
| type | event_type | text |
| title | title | text |

## Nullability Strategy

The validated snapshot contained 213 features.

Observed fully-null properties:

- `alert`
- `tz`

Observed partially-null properties:

- `cdi`
- `felt`
- `mmi`

The remaining profiled properties were populated in the validated snapshot.

However, raw-layer source columns should remain permissive unless a field is
required for technical integrity.

This prevents future source variability from causing ingestion failure.

The strict requirements are:

- `ingestion_run_id` NOT NULL
- `ingested_at` NOT NULL
- `event_id` NOT NULL

Source-level completeness rules belong primarily in dbt staging tests rather
than the raw loader.

## Temporal Handling

USGS provides `time` and `updated` as integer Unix epoch values in
milliseconds.

The raw relational layer preserves those values as:

- `event_time_epoch_ms bigint`
- `updated_time_epoch_ms bigint`

Timestamp conversion belongs in:

`stg_usgs__earthquakes`

This preserves source fidelity and prevents transformation logic from leaking
into the raw loader.

## Numeric Handling

The source JSON may represent numerically equivalent values using either JSON
integer or floating-point syntax.

Examples observed:

- `mag`: integer and float
- `dmin`: integer and float
- `rms`: integer and float
- `cdi`: integer and float

These fields are therefore represented using PostgreSQL `double precision`
where fractional values are possible.

## Historical Behavior

Raw relational loading must support repeated ingestion runs.

Example:

Run A:
`(run_a, nc75435042)`

Run B:
`(run_b, nc75435042)`

Both records may coexist.

This allows:

- snapshot comparison
- replay
- source-update analysis
- auditability
- deterministic dbt processing

## Relational Integrity

Recommended primary key:

`PRIMARY KEY (ingestion_run_id, event_id)`

Recommended foreign key:

`ingestion_run_id REFERENCES pipeline_runs(run_id)`

## Transformation Boundary

The raw layer must not:

- classify magnitude
- convert epoch values into analytical timestamps
- derive calendar attributes
- aggregate events
- apply geographic classifications
- implement BI-oriented logic

Those responsibilities belong to dbt staging, intermediate, and mart models.

## Validated Source Profile

Snapshot run:

`3d13fd9d-7146-4cf2-8dd3-3da7a74013cf`

Feature count:

`213`

Observed top-level feature keys:

- `geometry`
- `id`
- `properties`
- `type`

Observed geometry:

- type: `Point`
- coordinate count: `3`

Sample event identifier:

`nc75435042`

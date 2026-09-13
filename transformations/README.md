# dbt Transformation Project

This directory contains the analytical transformation layer for the Data
Platform Engineering Lab.

## Architecture

    raw.usgs_earthquakes
            ↓
    staging.stg_usgs__earthquakes
            ↓
    marts.fct_earthquake_events

The raw relational layer is loaded from immutable USGS GeoJSON snapshots.

dbt owns the analytical transformation layer:

- staging normalization
- timestamp conversion
- analytical derivations
- data quality tests
- documentation
- lineage

## Local Requirements

The local PostgreSQL service must be running.

The dbt profile reads the following environment variables:

- `POSTGRES_HOST`
- `POSTGRES_PORT`
- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`

Secrets are not committed to Git.

## Validate Connection

From the repository root:

    uv run dbt debug \
      --project-dir transformations \
      --profiles-dir transformations

## Build the Transformation Graph

    uv run dbt build \
      --project-dir transformations \
      --profiles-dir transformations

A successful build validates both models and data tests.

Current validated baseline:

- 2 dbt models
- 15 data tests
- 17 successful build resources
- 0 warnings
- 0 errors

## Generate Documentation and Lineage

    uv run dbt docs generate \
      --project-dir transformations \
      --profiles-dir transformations

Generated artifacts are written to:

`transformations/target/`

The generated directory is intentionally excluded from Git.

To inspect the documentation locally:

    uv run dbt docs serve \
      --project-dir transformations \
      --profiles-dir transformations

## Current Models

### `staging.stg_usgs__earthquakes`

Grain:

`(ingestion_run_id, event_id)`

Responsibilities:

- preserve snapshot history
- normalize source fields
- convert Unix epoch milliseconds to PostgreSQL timestamps
- remain close to the source representation

### `marts.fct_earthquake_events`

Grain:

`event_id`

Responsibilities:

- expose the latest known representation of each earthquake event
- derive UTC date and hour attributes
- derive magnitude classifications
- expose a boolean tsunami indicator
- preserve traceability to the latest ingestion run

## Data Quality

The current dbt project validates:

- required identifiers
- required timestamps
- snapshot grain uniqueness
- final mart event uniqueness
- GeoJSON feature type
- GeoJSON geometry type
- accepted magnitude classifications
- required lineage metadata

## Cost

The local dbt workflow uses PostgreSQL running in Docker and does not require
paid cloud infrastructure.

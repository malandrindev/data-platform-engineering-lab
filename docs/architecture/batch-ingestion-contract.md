# Batch Ingestion Contract

## Pipeline

`usgs-earthquakes`

## Purpose

Ingest public earthquake event data from the USGS Earthquake Hazards Program
into the local data platform.

The source payload will be preserved unchanged in the Raw / Landing layer,
while operational execution metadata will be stored separately.

## Source

Provider:

- U.S. Geological Survey (USGS)

Format:

- GeoJSON

Authentication:

- None

## Ingestion Flow

    USGS REST API
          |
          v
    Python Ingestion Service
          |
          +--> Azure Blob / Azurite
          |      Raw source payload
          |
          +--> PostgreSQL
                 Pipeline execution metadata


## Raw Storage Contract

Raw data must be stored without business transformation.

Target storage:

- Local: Azurite Blob Storage
- Future Azure target: Azure Blob Storage / ADLS Gen2

Container:

`raw`

Blob naming convention:

`usgs-earthquakes/YYYY/MM/DD/<run_id>.json`

Example:

`usgs-earthquakes/2026/09/13/550e8400-e29b-41d4-a716-446655440000.json`

## Operational Metadata

Each ingestion execution will generate a unique `run_id`.

Minimum metadata to record in PostgreSQL:

- run_id
- pipeline_name
- source_url
- started_at
- completed_at
- status
- records_received
- raw_blob_path
- error_message

## Status Values

Supported statuses:

- `running`
- `succeeded`
- `failed`

## Idempotency

Each execution receives a unique run identifier.

Raw source payloads are immutable once successfully written.

A retry creates a new execution record rather than silently overwriting the
previous ingestion attempt.

## Failure Behaviour

If source retrieval fails:

- raw data must not be written
- execution status becomes `failed`
- failure reason is recorded

If Blob upload fails:

- execution status becomes `failed`
- PostgreSQL metadata records the failure

If metadata persistence fails:

- the process must return a non-zero exit status

## Security

- No corporate or confidential data
- No credentials embedded in source code
- Runtime configuration provided through environment variables
- Real secrets must never be committed to Git

## Initial Success Criteria

The first pipeline is complete when it can:

1. Retrieve public USGS JSON data
2. Generate a unique pipeline run ID
3. Store the unchanged source payload in the Raw Blob layer
4. Record execution metadata in PostgreSQL
5. Report success or failure through process exit status
6. Pass Ruff, mypy and pytest
7. Pass GitHub Actions CI

# Transformation Layer Contract

## Objective

Define the transformation architecture for the local data platform and establish
clear responsibilities between raw ingestion, warehouse loading, dbt models,
and analytical outputs.

The transformation layer must remain reproducible, testable, observable, and
compatible with the zero-cost-first local platform.

## Architecture

USGS REST API
    ↓
Python ingestion
    ↓
Azurite raw immutable GeoJSON
    ↓
PostgreSQL raw relational layer
    ↓
dbt staging
    ↓
dbt intermediate
    ↓
dbt marts
    ↓
Analytical consumption

## Layer Responsibilities

### Raw Blob

Purpose:

- preserve the original source payload
- provide immutable historical evidence
- enable replay and recovery
- remain unchanged after ingestion

Storage:

- Azurite locally
- Azure Blob / ADLS Gen2 in a future cloud deployment

The raw Blob is the source-of-truth snapshot for each ingestion run.

### PostgreSQL Raw Schema

Schema:

`raw`

Purpose:

- expose source records in relational form
- preserve source-level attributes with minimal interpretation
- provide an efficient SQL-accessible input for dbt

Rules:

- loading raw relational data is not an analytical transformation
- source values should remain as close as practical to the source representation
- technical ingestion metadata may be added
- analytical business logic must not live in this layer

Initial target table:

`raw.usgs_earthquakes`

Expected technical metadata:

- ingestion_run_id
- ingested_at

Expected source fields include:

- earthquake identifier
- event timestamp
- updated timestamp
- magnitude
- place
- longitude
- latitude
- depth
- source/network attributes
- event type
- status

The exact schema will be defined from the USGS payload before implementation.

## dbt Staging Layer

Schema convention:

`staging`

Model naming:

`stg_<source>__<entity>`

Initial model:

`stg_usgs__earthquakes`

Responsibilities:

- rename source fields into consistent analytical names
- apply explicit data types
- normalize timestamps
- standardize null handling
- expose clean source-level records
- avoid business aggregation

Staging models should remain close to one source entity.

## dbt Intermediate Layer

Schema convention:

`intermediate`

Model naming:

`int_<domain>__<purpose>`

Responsibilities:

- reusable transformation logic
- derived attributes
- reusable joins
- classification logic
- preparation for analytical models

Intermediate models must not be considered final consumption interfaces.

## dbt Mart Layer

Schema convention:

`marts`

Responsibilities:

- analytical consumption
- dimensional or business-oriented models
- stable interfaces for BI and downstream analytics

Initial analytical candidates:

- earthquake event fact model
- date/time dimensions if justified
- magnitude classification
- geographic analysis attributes

The final dimensional design must be driven by analytical requirements rather
than creating dimensions without a clear use case.

## Transformation Principles

### Separation of Concerns

Python owns:

- source retrieval
- raw persistence
- operational ingestion metadata
- relational raw loading

dbt owns:

- SQL transformations
- analytical data quality rules
- model documentation
- lineage
- analytical model dependencies

### Immutability

Raw Blob payloads are immutable.

dbt transformations must never modify raw source payloads.

### Reproducibility

A transformation must be reproducible from persisted source data.

### Idempotency

Re-running transformation models with unchanged inputs must produce logically
equivalent outputs.

### Data Quality

Tests should cover, where applicable:

- uniqueness
- not-null constraints
- accepted values
- relationships
- domain-specific assertions

### Documentation

Each production-facing dbt model must document:

- purpose
- grain
- primary business key or technical key
- important columns
- upstream dependencies

## Initial Delivery Scope

Phase 8 initial scope:

1. define the PostgreSQL raw relational schema
2. load persisted USGS earthquake data into the raw schema
3. install and configure dbt for PostgreSQL
4. create staging models
5. create at least one analytical mart
6. implement dbt tests
7. generate dbt documentation and lineage
8. validate the complete transformation workflow through CI

## Deferred Scope

Not required for the initial Phase 8 foundation:

- Spark
- distributed compute
- production cloud warehouse
- incremental dbt models unless justified by data volume or architecture
- semantic model implementation
- BI dashboard development

## Success Criteria

Phase 8 foundation is successful when:

- raw source records are queryable in PostgreSQL
- dbt connects to PostgreSQL without secrets committed to Git
- staging models build successfully
- analytical models build successfully
- dbt tests pass
- lineage is generated
- transformation logic is version controlled
- CI validates the dbt project
- local execution remains zero-cost

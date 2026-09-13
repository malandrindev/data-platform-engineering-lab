import json
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

import httpx
from azure.storage.blob import ContainerClient
from psycopg import Connection

from data_platform.ingestion.blob import build_raw_blob_path, upload_raw_payload
from data_platform.ingestion.metadata import (
    complete_pipeline_run,
    create_pipeline_run,
    ensure_pipeline_runs_table,
)
from data_platform.ingestion.usgs import USGS_FEED_URL, fetch_usgs_payload

PIPELINE_NAME = "usgs-earthquakes"


def utc_now() -> datetime:
    return datetime.now(UTC)


def count_geojson_features(payload: bytes) -> int:
    document: object = json.loads(payload)

    if not isinstance(document, dict):
        raise ValueError("GeoJSON payload must be a JSON object")

    features = document.get("features")

    if not isinstance(features, list):
        raise ValueError("GeoJSON payload must contain a features list")

    return len(features)


def run_usgs_ingestion(
    *,
    http_client: httpx.Client,
    container: ContainerClient,
    connection: Connection[Any],
    now: Callable[[], datetime] = utc_now,
    run_id_factory: Callable[[], UUID] = uuid4,
) -> UUID:
    run_id = run_id_factory()
    started_at = now()

    ensure_pipeline_runs_table(connection)

    create_pipeline_run(
        connection,
        run_id=run_id,
        pipeline_name=PIPELINE_NAME,
        source_url=USGS_FEED_URL,
        started_at=started_at,
    )

    try:
        payload = fetch_usgs_payload(http_client)
        records_received = count_geojson_features(payload)

        blob_path = build_raw_blob_path(
            pipeline_name=PIPELINE_NAME,
            run_id=run_id,
            started_at=started_at,
        )

        upload_raw_payload(
            container=container,
            blob_path=blob_path,
            payload=payload,
        )

    except Exception as exc:
        complete_pipeline_run(
            connection,
            run_id=run_id,
            completed_at=now(),
            status="failed",
            records_received=None,
            raw_blob_path=None,
            error_message=str(exc),
        )
        raise

    complete_pipeline_run(
        connection,
        run_id=run_id,
        completed_at=now(),
        status="succeeded",
        records_received=records_received,
        raw_blob_path=blob_path,
        error_message=None,
    )

    return run_id

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch
from uuid import UUID

import httpx
import pytest
from azure.storage.blob import ContainerClient
from psycopg import Connection

from data_platform.ingestion.pipeline import (
    PIPELINE_NAME,
    count_geojson_features,
    run_usgs_ingestion,
    utc_now,
)
from data_platform.ingestion.usgs import USGS_FEED_URL


def test_utc_now_returns_timezone_aware_datetime() -> None:
    result = utc_now()

    assert result.tzinfo is not None
    assert result.utcoffset() == UTC.utcoffset(result)


def test_count_geojson_features() -> None:
    payload = b'{"type":"FeatureCollection","features":[{},{}]}'

    assert count_geojson_features(payload) == 2


def test_count_geojson_features_rejects_non_object() -> None:
    with pytest.raises(ValueError, match="JSON object"):
        count_geojson_features(b"[]")


def test_count_geojson_features_requires_features_list() -> None:
    with pytest.raises(ValueError, match="features list"):
        count_geojson_features(b'{"features":"invalid"}')


def test_run_usgs_ingestion_succeeds() -> None:
    connection = MagicMock(spec=Connection)
    container = MagicMock(spec=ContainerClient)
    http_client = MagicMock(spec=httpx.Client)

    run_id = UUID("550e8400-e29b-41d4-a716-446655440000")
    started_at = datetime(2026, 9, 13, 17, 0, tzinfo=UTC)
    completed_at = datetime(2026, 9, 13, 17, 1, tzinfo=UTC)

    times = iter([started_at, completed_at])

    def now() -> datetime:
        return next(times)

    def run_id_factory() -> UUID:
        return run_id

    payload = b'{"type":"FeatureCollection","features":[{},{}]}'
    blob_path = (
        "usgs-earthquakes/2026/09/13/"
        "550e8400-e29b-41d4-a716-446655440000.json"
    )

    with (
        patch(
            "data_platform.ingestion.pipeline.ensure_pipeline_runs_table"
        ) as ensure_table,
        patch(
            "data_platform.ingestion.pipeline.create_pipeline_run"
        ) as create_run,
        patch(
            "data_platform.ingestion.pipeline.fetch_usgs_payload",
            return_value=payload,
        ) as fetch_payload,
        patch(
            "data_platform.ingestion.pipeline.build_raw_blob_path",
            return_value=blob_path,
        ) as build_path,
        patch(
            "data_platform.ingestion.pipeline.upload_raw_payload"
        ) as upload_payload,
        patch(
            "data_platform.ingestion.pipeline.complete_pipeline_run"
        ) as complete_run,
    ):
        result = run_usgs_ingestion(
            http_client=http_client,
            container=container,
            connection=connection,
            now=now,
            run_id_factory=run_id_factory,
        )

    assert result == run_id

    ensure_table.assert_called_once_with(connection)

    create_run.assert_called_once_with(
        connection,
        run_id=run_id,
        pipeline_name=PIPELINE_NAME,
        source_url=USGS_FEED_URL,
        started_at=started_at,
    )

    fetch_payload.assert_called_once_with(
        http_client,
        url=USGS_FEED_URL,
    )

    build_path.assert_called_once_with(
        pipeline_name=PIPELINE_NAME,
        run_id=run_id,
        started_at=started_at,
    )

    upload_payload.assert_called_once_with(
        container=container,
        blob_path=blob_path,
        payload=payload,
    )

    complete_run.assert_called_once_with(
        connection,
        run_id=run_id,
        completed_at=completed_at,
        status="succeeded",
        records_received=2,
        raw_blob_path=blob_path,
        error_message=None,
    )


def test_run_usgs_ingestion_records_failure() -> None:
    connection = MagicMock(spec=Connection)
    container = MagicMock(spec=ContainerClient)
    http_client = MagicMock(spec=httpx.Client)

    run_id = UUID("550e8400-e29b-41d4-a716-446655440000")
    started_at = datetime(2026, 9, 13, 17, 0, tzinfo=UTC)
    failed_at = datetime(2026, 9, 13, 17, 1, tzinfo=UTC)

    times = iter([started_at, failed_at])

    def now() -> datetime:
        return next(times)

    def run_id_factory() -> UUID:
        return run_id

    with (
        patch("data_platform.ingestion.pipeline.ensure_pipeline_runs_table"),
        patch("data_platform.ingestion.pipeline.create_pipeline_run"),
        patch(
            "data_platform.ingestion.pipeline.fetch_usgs_payload",
            side_effect=RuntimeError("source unavailable"),
        ),
        patch(
            "data_platform.ingestion.pipeline.upload_raw_payload"
        ) as upload_payload,
        patch(
            "data_platform.ingestion.pipeline.complete_pipeline_run"
        ) as complete_run,pytest.raises(RuntimeError, match="source unavailable")
    ):
        run_usgs_ingestion(
            http_client=http_client,
            container=container,
            connection=connection,
            now=now,
            run_id_factory=run_id_factory,
        )

    upload_payload.assert_not_called()

    complete_run.assert_called_once_with(
        connection,
        run_id=run_id,
        completed_at=failed_at,
        status="failed",
        records_received=None,
        raw_blob_path=None,
        error_message="source unavailable",
    )

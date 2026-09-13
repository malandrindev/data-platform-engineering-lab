from datetime import UTC, datetime
from unittest.mock import MagicMock
from uuid import UUID

import pytest
from azure.storage.blob import ContainerClient

from data_platform.ingestion.blob import build_raw_blob_path, upload_raw_payload


def test_build_raw_blob_path() -> None:
    run_id = UUID("550e8400-e29b-41d4-a716-446655440000")
    started_at = datetime(2026, 9, 13, 15, 30, tzinfo=UTC)

    result = build_raw_blob_path(
        pipeline_name="usgs-earthquakes",
        run_id=run_id,
        started_at=started_at,
    )

    assert result == (
        "usgs-earthquakes/2026/09/13/"
        "550e8400-e29b-41d4-a716-446655440000.json"
    )


def test_build_raw_blob_path_rejects_naive_datetime() -> None:
    run_id = UUID("550e8400-e29b-41d4-a716-446655440000")
    started_at = datetime(2026, 9, 13, 15, 30)

    with pytest.raises(ValueError, match="timezone-aware"):
        build_raw_blob_path(
            pipeline_name="usgs-earthquakes",
            run_id=run_id,
            started_at=started_at,
        )


def test_upload_raw_payload() -> None:
    container = MagicMock(spec=ContainerClient)
    blob = container.get_blob_client.return_value
    payload = b'{"type":"FeatureCollection"}'

    upload_raw_payload(
        container=container,
        blob_path="usgs-earthquakes/2026/09/13/run.json",
        payload=payload,
    )

    container.get_blob_client.assert_called_once_with(
        "usgs-earthquakes/2026/09/13/run.json"
    )

    blob.upload_blob.assert_called_once()
    call = blob.upload_blob.call_args

    assert call.args[0] == payload
    assert call.kwargs["overwrite"] is False
    assert call.kwargs["content_settings"].content_type == "application/geo+json"

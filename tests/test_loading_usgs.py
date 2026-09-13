from datetime import UTC, datetime
from unittest.mock import MagicMock
from uuid import UUID

import pytest
from azure.storage.blob import ContainerClient
from psycopg import Connection

from data_platform.loading.usgs import (
    COUNT_RAW_USGS_SQL,
    INSERT_RAW_USGS_SQL,
    load_usgs_blob_to_raw,
)


def test_load_usgs_blob_to_raw_succeeds() -> None:
    connection = MagicMock(spec=Connection)
    container = MagicMock(spec=ContainerClient)

    cursor = connection.cursor.return_value.__enter__.return_value

    blob = container.get_blob_client.return_value
    download = blob.download_blob.return_value

    payload = (
        b'{"type":"FeatureCollection","features":'
        b'[{"id":"event-1"},{"id":"event-2"}]}'
    )
    download.readall.return_value = payload

    cursor.fetchone.return_value = (2,)

    run_id = UUID("550e8400-e29b-41d4-a716-446655440000")
    ingested_at = datetime(2026, 9, 13, 19, 0, tzinfo=UTC)
    blob_path = "usgs-earthquakes/2026/09/13/run.json"

    result = load_usgs_blob_to_raw(
        connection,
        container,
        run_id=run_id,
        blob_path=blob_path,
        ingested_at=ingested_at,
    )

    assert result == 2

    container.get_blob_client.assert_called_once_with(blob_path)
    download.readall.assert_called_once_with()

    assert cursor.execute.call_count == 2

    cursor.execute.assert_any_call(
        INSERT_RAW_USGS_SQL,
        (
            payload.decode("utf-8"),
            run_id,
            ingested_at,
        ),
    )

    cursor.execute.assert_any_call(
        COUNT_RAW_USGS_SQL,
        (run_id,),
    )

    connection.commit.assert_called_once_with()
    connection.rollback.assert_not_called()


def test_load_usgs_blob_to_raw_rejects_count_mismatch() -> None:
    connection = MagicMock(spec=Connection)
    container = MagicMock(spec=ContainerClient)

    cursor = connection.cursor.return_value.__enter__.return_value

    payload = (
        b'{"type":"FeatureCollection","features":'
        b'[{"id":"event-1"},{"id":"event-2"}]}'
    )

    container.get_blob_client.return_value.download_blob.return_value.readall.return_value = (
        payload
    )

    cursor.fetchone.return_value = (1,)

    run_id = UUID("550e8400-e29b-41d4-a716-446655440000")

    with pytest.raises(
        RuntimeError,
        match="expected 2 records, found 1",
    ):
        load_usgs_blob_to_raw(
            connection,
            container,
            run_id=run_id,
            blob_path="raw.json",
            ingested_at=datetime(2026, 9, 13, 19, 0, tzinfo=UTC),
        )

    connection.rollback.assert_called_once_with()
    connection.commit.assert_not_called()


def test_load_usgs_blob_to_raw_rejects_missing_validation_result() -> None:
    connection = MagicMock(spec=Connection)
    container = MagicMock(spec=ContainerClient)

    cursor = connection.cursor.return_value.__enter__.return_value

    container.get_blob_client.return_value.download_blob.return_value.readall.return_value = (
        b'{"type":"FeatureCollection","features":[]}'
    )

    cursor.fetchone.return_value = None

    with pytest.raises(
        RuntimeError,
        match="Could not validate raw USGS load",
    ):
        load_usgs_blob_to_raw(
            connection,
            container,
            run_id=UUID("550e8400-e29b-41d4-a716-446655440000"),
            blob_path="raw.json",
            ingested_at=datetime(2026, 9, 13, 19, 0, tzinfo=UTC),
        )

    connection.rollback.assert_called_once_with()
    connection.commit.assert_not_called()

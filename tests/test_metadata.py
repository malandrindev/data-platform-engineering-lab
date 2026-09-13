from datetime import UTC, datetime
from unittest.mock import MagicMock
from uuid import UUID

import pytest
from psycopg import Connection

from data_platform.ingestion.metadata import (
    CREATE_PIPELINE_RUNS_TABLE_SQL,
    INSERT_PIPELINE_RUN_SQL,
    UPDATE_PIPELINE_RUN_SQL,
    complete_pipeline_run,
    create_pipeline_run,
    ensure_pipeline_runs_table,
)


def test_ensure_pipeline_runs_table() -> None:
    connection = MagicMock(spec=Connection)
    cursor = connection.cursor.return_value.__enter__.return_value

    ensure_pipeline_runs_table(connection)

    cursor.execute.assert_called_once_with(CREATE_PIPELINE_RUNS_TABLE_SQL)
    connection.commit.assert_called_once_with()


def test_create_pipeline_run() -> None:
    connection = MagicMock(spec=Connection)
    cursor = connection.cursor.return_value.__enter__.return_value

    run_id = UUID("550e8400-e29b-41d4-a716-446655440000")
    started_at = datetime(2026, 9, 13, 16, 0, tzinfo=UTC)

    create_pipeline_run(
        connection,
        run_id=run_id,
        pipeline_name="usgs-earthquakes",
        source_url="https://example.com/feed.geojson",
        started_at=started_at,
    )

    cursor.execute.assert_called_once_with(
        INSERT_PIPELINE_RUN_SQL,
        (
            run_id,
            "usgs-earthquakes",
            "https://example.com/feed.geojson",
            started_at,
        ),
    )

    connection.commit.assert_called_once_with()


def test_complete_pipeline_run() -> None:
    connection = MagicMock(spec=Connection)
    cursor = connection.cursor.return_value.__enter__.return_value

    run_id = UUID("550e8400-e29b-41d4-a716-446655440000")
    completed_at = datetime(2026, 9, 13, 16, 5, tzinfo=UTC)

    complete_pipeline_run(
        connection,
        run_id=run_id,
        completed_at=completed_at,
        status="succeeded",
        records_received=42,
        raw_blob_path="usgs-earthquakes/2026/09/13/run.json",
        error_message=None,
    )

    cursor.execute.assert_called_once_with(
        UPDATE_PIPELINE_RUN_SQL,
        (
            completed_at,
            "succeeded",
            42,
            "usgs-earthquakes/2026/09/13/run.json",
            None,
            run_id,
        ),
    )

    connection.commit.assert_called_once_with()


def test_complete_pipeline_run_rejects_invalid_status() -> None:
    connection = MagicMock(spec=Connection)

    with pytest.raises(ValueError, match="status must be"):
        complete_pipeline_run(
            connection,
            run_id=UUID("550e8400-e29b-41d4-a716-446655440000"),
            completed_at=datetime(2026, 9, 13, 16, 5, tzinfo=UTC),
            status="running",
            records_received=None,
            raw_blob_path=None,
            error_message=None,
        )

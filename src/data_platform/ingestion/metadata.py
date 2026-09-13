from datetime import datetime
from typing import Any
from uuid import UUID

from psycopg import Connection

CREATE_PIPELINE_RUNS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS pipeline_runs (
    run_id uuid PRIMARY KEY,
    pipeline_name text NOT NULL,
    source_url text NOT NULL,
    started_at timestamptz NOT NULL,
    completed_at timestamptz,
    status text NOT NULL CHECK (status IN ('running', 'succeeded', 'failed')),
    records_received integer,
    raw_blob_path text,
    error_message text
);
"""


def ensure_pipeline_runs_table(connection: Connection[Any]) -> None:
    with connection.cursor() as cursor:
        cursor.execute(CREATE_PIPELINE_RUNS_TABLE_SQL)

    connection.commit()


INSERT_PIPELINE_RUN_SQL = """
INSERT INTO pipeline_runs (
    run_id,
    pipeline_name,
    source_url,
    started_at,
    status
)
VALUES (%s, %s, %s, %s, 'running');
"""


def create_pipeline_run(
    connection: Connection[Any],
    *,
    run_id: UUID,
    pipeline_name: str,
    source_url: str,
    started_at: datetime,
) -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            INSERT_PIPELINE_RUN_SQL,
            (
                run_id,
                pipeline_name,
                source_url,
                started_at,
            ),
        )

    connection.commit()


UPDATE_PIPELINE_RUN_SQL = """
UPDATE pipeline_runs
SET
    completed_at = %s,
    status = %s,
    records_received = %s,
    raw_blob_path = %s,
    error_message = %s
WHERE run_id = %s;
"""


def complete_pipeline_run(
    connection: Connection[Any],
    *,
    run_id: UUID,
    completed_at: datetime,
    status: str,
    records_received: int | None,
    raw_blob_path: str | None,
    error_message: str | None,
) -> None:
    if status not in {"succeeded", "failed"}:
        raise ValueError("status must be 'succeeded' or 'failed'")

    with connection.cursor() as cursor:
        cursor.execute(
            UPDATE_PIPELINE_RUN_SQL,
            (
                completed_at,
                status,
                records_received,
                raw_blob_path,
                error_message,
                run_id,
            ),
        )

    connection.commit()

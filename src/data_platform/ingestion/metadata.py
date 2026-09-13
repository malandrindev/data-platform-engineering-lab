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

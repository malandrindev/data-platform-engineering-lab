from unittest.mock import MagicMock

from psycopg import Connection

from data_platform.ingestion.metadata import (
    CREATE_PIPELINE_RUNS_TABLE_SQL,
    ensure_pipeline_runs_table,
)


def test_ensure_pipeline_runs_table() -> None:
    connection = MagicMock(spec=Connection)
    cursor = connection.cursor.return_value.__enter__.return_value

    ensure_pipeline_runs_table(connection)

    cursor.execute.assert_called_once_with(CREATE_PIPELINE_RUNS_TABLE_SQL)
    connection.commit.assert_called_once_with()

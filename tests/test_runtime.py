from unittest.mock import MagicMock, patch
from uuid import UUID

import pytest
from azure.core.exceptions import ResourceExistsError

from data_platform.ingestion.runtime import (
    RuntimeConfig,
    get_raw_container,
    main,
    run_from_environment,
)


def set_valid_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("POSTGRES_HOST", "127.0.0.1")
    monkeypatch.setenv("POSTGRES_PORT", "5432")
    monkeypatch.setenv("POSTGRES_DB", "data_platform")
    monkeypatch.setenv("POSTGRES_USER", "data_platform")
    monkeypatch.setenv("POSTGRES_PASSWORD", "test-password")
    monkeypatch.setenv(
        "AZURE_STORAGE_CONNECTION_STRING",
        "UseDevelopmentStorage=true",
    )


def test_runtime_config_from_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    set_valid_environment(monkeypatch)

    config = RuntimeConfig.from_environment()

    assert config.postgres_host == "127.0.0.1"
    assert config.postgres_port == 5432
    assert config.postgres_db == "data_platform"
    assert config.postgres_user == "data_platform"
    assert config.postgres_password == "test-password"
    assert config.azure_storage_connection_string == "UseDevelopmentStorage=true"


def test_runtime_config_rejects_missing_variables(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    set_valid_environment(monkeypatch)
    monkeypatch.delenv("POSTGRES_PASSWORD")

    with pytest.raises(
        RuntimeError,
        match="POSTGRES_PASSWORD",
    ):
        RuntimeConfig.from_environment()


def test_runtime_config_rejects_invalid_port(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    set_valid_environment(monkeypatch)
    monkeypatch.setenv("POSTGRES_PORT", "invalid")

    with pytest.raises(
        RuntimeError,
        match="POSTGRES_PORT must be an integer",
    ):
        RuntimeConfig.from_environment()


def test_get_raw_container_creates_container() -> None:
    service = MagicMock()
    container = MagicMock()
    service.get_container_client.return_value = container

    with patch(
        "data_platform.ingestion.runtime.BlobServiceClient.from_connection_string",
        return_value=service,
    ) as create_service:
        result = get_raw_container("connection-string")

    assert result is container
    create_service.assert_called_once_with("connection-string")
    service.get_container_client.assert_called_once_with("raw")
    container.create_container.assert_called_once_with()


def test_get_raw_container_accepts_existing_container() -> None:
    service = MagicMock()
    container = MagicMock()
    container.create_container.side_effect = ResourceExistsError(
        message="already exists"
    )
    service.get_container_client.return_value = container

    with patch(
        "data_platform.ingestion.runtime.BlobServiceClient.from_connection_string",
        return_value=service,
    ):
        result = get_raw_container("connection-string")

    assert result is container
    container.create_container.assert_called_once_with()


def test_run_from_environment() -> None:
    config = RuntimeConfig(
        postgres_host="127.0.0.1",
        postgres_port=5432,
        postgres_db="data_platform",
        postgres_user="data_platform",
        postgres_password="test-password",
        azure_storage_connection_string="connection-string",
    )

    container = MagicMock()
    connection = MagicMock()
    http_client = MagicMock()

    postgres_context = MagicMock()
    postgres_context.__enter__.return_value = connection

    http_context = MagicMock()
    http_context.__enter__.return_value = http_client

    run_id = UUID("550e8400-e29b-41d4-a716-446655440000")

    with (
        patch("data_platform.ingestion.runtime.load_dotenv") as load_env,
        patch.object(
            RuntimeConfig,
            "from_environment",
            return_value=config,
        ),
        patch(
            "data_platform.ingestion.runtime.get_raw_container",
            return_value=container,
        ),
        patch(
            "data_platform.ingestion.runtime.psycopg.connect",
            return_value=postgres_context,
        ) as connect,
        patch(
            "data_platform.ingestion.runtime.httpx.Client",
            return_value=http_context,
        ) as create_http_client,
        patch(
            "data_platform.ingestion.runtime.run_usgs_ingestion",
            return_value=run_id,
        ) as run_pipeline,
    ):
        result = run_from_environment()

    assert result == run_id

    load_env.assert_called_once_with()

    connect.assert_called_once_with(
        host="127.0.0.1",
        port=5432,
        dbname="data_platform",
        user="data_platform",
        password="test-password",
    )

    create_http_client.assert_called_once_with(timeout=30.0)

    run_pipeline.assert_called_once_with(
        http_client=http_client,
        container=container,
        connection=connection,
    )


def test_main_prints_run_id(capsys: pytest.CaptureFixture[str]) -> None:
    run_id = UUID("550e8400-e29b-41d4-a716-446655440000")

    with patch(
        "data_platform.ingestion.runtime.run_from_environment",
        return_value=run_id,
    ):
        main()

    captured = capsys.readouterr()

    assert captured.out == f"Pipeline run succeeded: {run_id}\n"

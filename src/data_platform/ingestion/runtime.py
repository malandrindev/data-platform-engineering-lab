import os
from contextlib import suppress
from dataclasses import dataclass
from typing import cast
from uuid import UUID

import httpx
import psycopg
from azure.core.exceptions import ResourceExistsError
from azure.storage.blob import BlobServiceClient, ContainerClient
from dotenv import load_dotenv

from data_platform.ingestion.blob import RAW_CONTAINER
from data_platform.ingestion.pipeline import run_usgs_ingestion


@dataclass(frozen=True, slots=True)
class RuntimeConfig:
    postgres_host: str
    postgres_port: int
    postgres_db: str
    postgres_user: str
    postgres_password: str
    azure_storage_connection_string: str

    @classmethod
    def from_environment(cls) -> "RuntimeConfig":
        required_variables = (
            "POSTGRES_HOST",
            "POSTGRES_PORT",
            "POSTGRES_DB",
            "POSTGRES_USER",
            "POSTGRES_PASSWORD",
            "AZURE_STORAGE_CONNECTION_STRING",
        )

        values = {
            variable: os.getenv(variable)
            for variable in required_variables
        }

        missing = [
            variable
            for variable, value in values.items()
            if not value
        ]

        if missing:
            raise RuntimeError(
                "Missing required environment variables: "
                + ", ".join(sorted(missing))
            )

        port_value = cast(str, values["POSTGRES_PORT"])

        try:
            postgres_port = int(port_value)
        except ValueError as exc:
            raise RuntimeError(
                "POSTGRES_PORT must be an integer"
            ) from exc

        return cls(
            postgres_host=cast(str, values["POSTGRES_HOST"]),
            postgres_port=postgres_port,
            postgres_db=cast(str, values["POSTGRES_DB"]),
            postgres_user=cast(str, values["POSTGRES_USER"]),
            postgres_password=cast(str, values["POSTGRES_PASSWORD"]),
            azure_storage_connection_string=cast(
                str,
                values["AZURE_STORAGE_CONNECTION_STRING"],
            ),
        )


def get_raw_container(connection_string: str) -> ContainerClient:
    service = BlobServiceClient.from_connection_string(
        connection_string
    )
    container = service.get_container_client(RAW_CONTAINER)

    with suppress(ResourceExistsError):
        container.create_container()

    return container


def run_from_environment() -> UUID:
    load_dotenv()

    config = RuntimeConfig.from_environment()

    container = get_raw_container(
        config.azure_storage_connection_string
    )

    with (
        psycopg.connect(
            host=config.postgres_host,
            port=config.postgres_port,
            dbname=config.postgres_db,
            user=config.postgres_user,
            password=config.postgres_password,
        ) as connection,
        httpx.Client(timeout=30.0) as http_client,
    ):
        return run_usgs_ingestion(
            http_client=http_client,
            container=container,
            connection=connection,
        )


def main() -> None:
    run_id = run_from_environment()
    print(f"Pipeline run succeeded: {run_id}")


if __name__ == "__main__":  # pragma: no cover
    main()

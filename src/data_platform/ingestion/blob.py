from datetime import UTC, datetime
from uuid import UUID

from azure.storage.blob import ContainerClient, ContentSettings

RAW_CONTAINER = "raw"


def build_raw_blob_path(
    pipeline_name: str,
    run_id: UUID,
    started_at: datetime,
) -> str:
    if started_at.tzinfo is None:
        raise ValueError("started_at must be timezone-aware")

    utc_started_at = started_at.astimezone(UTC)

    return (
        f"{pipeline_name}/"
        f"{utc_started_at:%Y/%m/%d}/"
        f"{run_id}.json"
    )


def upload_raw_payload(
    container: ContainerClient,
    blob_path: str,
    payload: bytes,
) -> None:
    blob = container.get_blob_client(blob_path)

    blob.upload_blob(
        payload,
        overwrite=False,
        content_settings=ContentSettings(
            content_type="application/geo+json",
        ),
    )

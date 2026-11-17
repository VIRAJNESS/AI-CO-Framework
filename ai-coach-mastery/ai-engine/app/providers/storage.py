"""Storage provider port + adapters.

Selected via STORAGE_PROVIDER env var:
  local      — filesystem (default; zero external dependencies)
  s3         — any S3-compatible endpoint (MinIO locally, AWS S3 in cloud)
  azure_blob — stub (Step-1 contract only)
  gcs        — stub (Step-1 contract only)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path, PurePosixPath

from app.core.config import Settings, StorageProviderName


class StorageProvider(ABC):
    """Port: artifact persistence contract."""

    name: str

    @abstractmethod
    def put(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        """Store bytes under key; return a retrievable locator (path or URL)."""

    @abstractmethod
    def get(self, key: str) -> bytes:
        """Retrieve bytes stored under key. Raises FileNotFoundError if absent."""


class LocalStorageProvider(StorageProvider):
    """Filesystem adapter (default). Keys map to paths under a root directory."""

    name = "local"

    def __init__(self, root: str) -> None:
        self._root = Path(root)
        self._root.mkdir(parents=True, exist_ok=True)

    def _resolve(self, key: str) -> Path:
        # Normalize + prevent path traversal outside the storage root.
        clean = PurePosixPath(key)
        if clean.is_absolute() or ".." in clean.parts:
            raise ValueError(f"Invalid storage key: {key}")
        return self._root / Path(*clean.parts)

    def put(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        path = self._resolve(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return str(path)

    def get(self, key: str) -> bytes:
        path = self._resolve(key)
        if not path.exists():
            raise FileNotFoundError(f"Artifact not found: {key}")
        return path.read_bytes()


class S3StorageProvider(StorageProvider):
    """S3-compatible adapter — works with MinIO locally and AWS S3 in cloud."""

    name = "s3"

    def __init__(self, endpoint: str, access_key: str, secret_key: str, bucket: str) -> None:
        # Imported lazily so the local provider needs no boto3 at runtime.
        import boto3

        self._bucket = bucket
        self._client = boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
        )

    def put(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        self._client.put_object(
            Bucket=self._bucket, Key=key, Body=data, ContentType=content_type
        )
        return f"s3://{self._bucket}/{key}"

    def get(self, key: str) -> bytes:
        try:
            response = self._client.get_object(Bucket=self._bucket, Key=key)
        except self._client.exceptions.NoSuchKey as exc:
            raise FileNotFoundError(f"Artifact not found: {key}") from exc
        return response["Body"].read()


class _UnconfiguredStorageProvider(StorageProvider):
    """Stub for azure_blob / gcs — fails fast with an actionable message."""

    def __init__(self, name: str) -> None:
        self.name = name

    def _fail(self) -> None:
        raise NotImplementedError(
            f"Storage provider '{self.name}' adapter is a Step-1 stub. "
            f"Set STORAGE_PROVIDER=local (default) or s3 for local development."
        )

    def put(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        self._fail()
        return ""  # unreachable

    def get(self, key: str) -> bytes:
        self._fail()
        return b""  # unreachable


def get_storage_provider(settings: Settings) -> StorageProvider:
    """Factory: resolve the configured storage backend (12-factor switch)."""
    if settings.storage_provider == StorageProviderName.LOCAL:
        return LocalStorageProvider(settings.local_storage_path)
    if settings.storage_provider == StorageProviderName.S3:
        return S3StorageProvider(
            endpoint=settings.s3_endpoint,
            access_key=settings.s3_access_key,
            secret_key=settings.s3_secret_key,
            bucket=settings.s3_bucket,
        )
    return _UnconfiguredStorageProvider(settings.storage_provider.value)

import base64
import json
import uuid
from datetime import timedelta

from google.cloud import storage
from google.oauth2 import service_account

from app.core.config import settings

_GCS_SCOPES = ["https://www.googleapis.com/auth/cloud-platform"]
_SIGNED_URL_TTL = timedelta(minutes=15)


class GcsService:
    def __init__(self, bucket_name: str, credentials_b64: str) -> None:
        self._bucket_name = bucket_name
        self._credentials_b64 = credentials_b64
        self._credentials: service_account.Credentials | None = None
        self._client: storage.Client | None = None

    @property
    def enabled(self) -> bool:
        return bool(self._bucket_name and self._credentials_b64)

    def _get_credentials(self) -> service_account.Credentials:
        if self._credentials is None:
            info = json.loads(base64.b64decode(self._credentials_b64))
            self._credentials = service_account.Credentials.from_service_account_info(
                info, scopes=_GCS_SCOPES
            )
        return self._credentials

    def _get_client(self) -> storage.Client:
        if self._client is None:
            creds = self._get_credentials()
            info = json.loads(base64.b64decode(self._credentials_b64))
            self._client = storage.Client(credentials=creds, project=info["project_id"])
        return self._client

    def _make_blob_name(self, product_id: int, filename: str) -> str:
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "jpg"
        return f"products/{product_id}/{uuid.uuid4().hex}.{ext}"

    def public_url(self, blob_name: str) -> str:
        return f"https://storage.googleapis.com/{self._bucket_name}/{blob_name}"

    def sign_upload(
        self, product_id: int, filename: str, content_type: str
    ) -> dict[str, str]:
        blob_name = self._make_blob_name(product_id, filename)
        client = self._get_client()
        bucket = client.bucket(self._bucket_name)
        blob = bucket.blob(blob_name)
        signed_url = blob.generate_signed_url(
            version="v4",
            expiration=_SIGNED_URL_TTL,
            method="PUT",
            content_type=content_type,
            credentials=self._get_credentials(),
        )
        return {"signed_url": signed_url, "public_url": self.public_url(blob_name)}

    def delete_object(self, public_url: str) -> None:
        prefix = f"https://storage.googleapis.com/{self._bucket_name}/"
        if not public_url.startswith(prefix):
            return
        blob_name = public_url[len(prefix):]
        client = self._get_client()
        bucket = client.bucket(self._bucket_name)
        blob = bucket.blob(blob_name)
        blob.delete()


gcs_service = GcsService(
    bucket_name=settings.gcs_bucket_name,
    credentials_b64=settings.gcs_credentials_b64,
)

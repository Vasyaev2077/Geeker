from django.conf import settings
import boto3
from .base import BaseStorageAdapter


class S3StorageAdapter(BaseStorageAdapter):
    def __init__(self):
        self.client = boto3.client(
            "s3",
            endpoint_url=getattr(settings, "S3_ENDPOINT", None),
            aws_access_key_id=getattr(settings, "S3_ACCESS_KEY", None),
            aws_secret_access_key=getattr(settings, "S3_SECRET_KEY", None),
            region_name=getattr(settings, "S3_REGION", None),
        )
        self.bucket = getattr(settings, "S3_BUCKET", "")

    def upload_file(self, file, path: str) -> str:
        self.client.upload_fileobj(
            file,
            self.bucket,
            path,
            ExtraArgs={"ACL": "public-read"},
        )
        base_url = getattr(settings, "S3_PUBLIC_URL", "")
        return f"{base_url}/{path}"

    def delete_file(self, path: str) -> None:
        self.client.delete_object(Bucket=self.bucket, Key=path)









"""POST /uploads -> presigned S3 PUT URL for a bin photo."""
import uuid

from lib import config, db, repo
from lib.http import AppError, api_handler, body_json, ok, parse
from lib.models import UploadRequest


def create_upload(event: dict) -> dict:
    req = parse(UploadRequest, body_json(event))
    ext = config.ALLOWED_UPLOAD_TYPES.get(req.contentType.lower())
    if not ext:
        raise AppError("UNSUPPORTED_TYPE", "Only JPEG or PNG photos are supported.", 415)
    repo.require_user(req.userId, role="household")
    key = f"scans/{req.userId}/{uuid.uuid4()}.{ext}"
    url = db.s3().generate_presigned_url(
        "put_object",
        Params={"Bucket": config.photo_bucket(), "Key": key, "ContentType": req.contentType.lower()},
        ExpiresIn=config.UPLOAD_URL_EXPIRY_S,
    )
    return ok({"uploadUrl": url, "imageKey": key, "contentType": req.contentType.lower(), "expiresIn": config.UPLOAD_URL_EXPIRY_S})


lambda_handler = api_handler({"POST /uploads": create_upload})

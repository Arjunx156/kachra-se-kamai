"""POST /scans (vision -> pricing -> save -> stats), GET /scans, GET /scans/{scanId}"""
from typing import Optional

from botocore.exceptions import ClientError

from lib import config, db, repo, scan_service, vision
from lib.http import AppError, api_handler, body_json, ok, parse, path_param, query
from lib.models import ScanRequest


def _image_url(scan: dict) -> Optional[str]:
    key = scan.get("imageKey")
    if not key:
        return None
    return db.s3().generate_presigned_url(
        "get_object", Params={"Bucket": config.photo_bucket(), "Key": key}, ExpiresIn=config.IMAGE_VIEW_URL_EXPIRY_S
    )


def _with_society(scan: dict) -> dict:
    society = repo.get_society(scan.get("societyId", "")) if scan.get("societyId") else None
    return {**scan, "societyName": society["name"] if society else None, "imageUrl": _image_url(scan)}


def _read_image(key: str) -> tuple[bytes, str]:
    bucket = config.photo_bucket()
    try:
        head = db.s3().head_object(Bucket=bucket, Key=key)
    except ClientError as exc:
        raise AppError("IMAGE_NOT_FOUND", "We couldn't find your uploaded photo. Please try uploading again.", 404) from exc
    if head.get("ContentLength", 0) > config.MAX_IMAGE_BYTES:
        raise AppError("IMAGE_TOO_LARGE", "That photo is too large (max 5 MB).", 413)
    body = db.s3().get_object(Bucket=bucket, Key=key)["Body"].read()
    return body, vision.image_format(head.get("ContentType"), key)


def create_scan(event: dict) -> dict:
    req = parse(ScanRequest, body_json(event))
    if not req.imageKey.startswith(f"scans/{req.userId}/") or ".." in req.imageKey:
        raise AppError("BAD_IMAGE_KEY", "That photo doesn't belong to this user.", 403)
    user = repo.require_user(req.userId, role="household")
    image, fmt = _read_image(req.imageKey)
    analysis = vision.analyze_image(image, fmt)
    scan = scan_service.record_scan(user, req.imageKey, analysis, repo.load_rates(), db.now_utc())
    return ok(_with_society(scan), 201)


def list_scans(event: dict) -> dict:
    user_id = query(event).get("userId", "")
    if not user_id:
        raise AppError("BAD_REQUEST", "userId is required.")
    return ok({"scans": repo.list_user_scans(user_id)})


def get_scan(event: dict) -> dict:
    user_id = query(event).get("userId", "")
    if not user_id:
        raise AppError("BAD_REQUEST", "userId is required.")
    scan = repo.get_scan(user_id, path_param(event, "scanId"))
    if not scan:
        raise AppError("SCAN_NOT_FOUND", "We couldn't find that scan.", 404)
    return ok(_with_society(scan))


lambda_handler = api_handler(
    {"POST /scans": create_scan, "GET /scans": list_scans, "GET /scans/{scanId}": get_scan}
)

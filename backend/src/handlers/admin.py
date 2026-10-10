"""POST /admin/seed, POST /admin/reset (protected by the x-admin-key header)."""
import hmac

from lib import config, seed
from lib.http import AppError, api_handler, header, ok


def _require_admin(event: dict) -> None:
    expected = config.admin_key()
    if not expected:
        raise AppError("ADMIN_DISABLED", "Admin endpoints are disabled (no AdminKey configured).", 503)
    if not hmac.compare_digest(header(event, "x-admin-key").encode(), expected.encode()):
        raise AppError("UNAUTHORIZED", "Invalid admin key.", 401)


def seed_data(event: dict) -> dict:
    _require_admin(event)
    wiped = seed.reset()
    return ok({**seed.run(), **wiped})


def reset_data(event: dict) -> dict:
    _require_admin(event)
    return ok(seed.reset())


lambda_handler = api_handler({"POST /admin/seed": seed_data, "POST /admin/reset": reset_data})

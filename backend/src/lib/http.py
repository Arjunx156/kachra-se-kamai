"""HTTP API (payload v2) helpers: response envelope, errors, body parsing."""
import base64
import json
import logging
from functools import wraps
from typing import Any, Callable, Type, TypeVar

from pydantic import BaseModel, ValidationError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

M = TypeVar("M", bound=BaseModel)

_HEADERS = {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"}


class AppError(Exception):
    """An expected error with a stable code and a user-friendly message."""

    def __init__(self, code: str, message: str, status: int = 400):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status


def ok(data: Any, status: int = 200) -> dict:
    return {"statusCode": status, "headers": _HEADERS, "body": json.dumps({"ok": True, "data": data}, default=str)}


def error(code: str, message: str, status: int = 400) -> dict:
    body = {"ok": False, "error": {"code": code, "message": message}}
    return {"statusCode": status, "headers": _HEADERS, "body": json.dumps(body)}


def body_json(event: dict) -> dict:
    raw = event.get("body") or ""
    if event.get("isBase64Encoded") and raw:
        raw = base64.b64decode(raw).decode("utf-8")
    if not raw:
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise AppError("BAD_JSON", "Request body must be valid JSON.") from exc
    if not isinstance(data, dict):
        raise AppError("BAD_JSON", "Request body must be a JSON object.")
    return data


def parse(model: Type[M], data: dict) -> M:
    return model.model_validate(data)


def query(event: dict) -> dict:
    return event.get("queryStringParameters") or {}


def path_param(event: dict, name: str) -> str:
    value = (event.get("pathParameters") or {}).get(name)
    if not value:
        raise AppError("BAD_REQUEST", f"Missing path parameter '{name}'.")
    return value


def header(event: dict, name: str) -> str:
    headers = event.get("headers") or {}
    lowered = {k.lower(): v for k, v in headers.items()}
    return lowered.get(name.lower(), "")


def route_key(event: dict) -> str:
    return event.get("routeKey", "")


def api_handler(routes: dict[str, Callable[[dict], dict]]) -> Callable[[dict, Any], dict]:
    """Build a Lambda handler that dispatches on routeKey and maps errors to the envelope."""

    @wraps(api_handler)
    def handler(event: dict, _context: Any) -> dict:
        key = route_key(event)
        fn = routes.get(key)
        if fn is None:
            return error("NOT_FOUND", f"No route for {key or 'request'}.", 404)
        try:
            return fn(event)
        except AppError as exc:
            logger.info("app_error route=%s code=%s msg=%s", key, exc.code, exc.message)
            return error(exc.code, exc.message, exc.status)
        except ValidationError as exc:
            fields = ", ".join(".".join(str(p) for p in e["loc"]) or "body" for e in exc.errors())
            logger.info("validation_error route=%s fields=%s", key, fields)
            return error("VALIDATION_ERROR", f"Please check these fields: {fields}.", 400)
        except Exception:  # noqa: BLE001 - last-resort guard; details go to logs only
            logger.exception("unhandled_error route=%s", key)
            return error("INTERNAL", "Something went wrong on our side. Please try again.", 500)

    return handler

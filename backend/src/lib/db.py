"""DynamoDB helpers: lazily created resources, float <-> Decimal conversion, pagination."""
import secrets
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Iterable

import boto3

from lib import config

_dynamodb: Any = None
_s3: Any = None


def dynamodb() -> Any:
    global _dynamodb
    if _dynamodb is None:
        _dynamodb = boto3.resource("dynamodb", region_name=config.aws_region())
    return _dynamodb


def s3() -> Any:
    global _s3
    if _s3 is None:
        from botocore.config import Config

        _s3 = boto3.client("s3", region_name=config.aws_region(), config=Config(signature_version="s3v4"))
    return _s3


def reset_clients() -> None:
    """Drop cached clients (used by tests that start a fresh AWS mock)."""
    global _dynamodb, _s3
    _dynamodb = None
    _s3 = None


def table(name: str) -> Any:
    return dynamodb().Table(name)


def to_ddb(obj: Any) -> Any:
    if isinstance(obj, bool) or obj is None:
        return obj
    if isinstance(obj, float):
        return Decimal(str(obj))
    if isinstance(obj, dict):
        return {k: to_ddb(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [to_ddb(v) for v in obj]
    return obj


def from_ddb(obj: Any) -> Any:
    if isinstance(obj, Decimal):
        return int(obj) if obj == obj.to_integral_value() else float(obj)
    if isinstance(obj, dict):
        return {k: from_ddb(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [from_ddb(v) for v in obj]
    return obj


def query_all(tbl: Any, **kwargs: Any) -> list[dict]:
    items: list[dict] = []
    while True:
        page = tbl.query(**kwargs)
        items.extend(page.get("Items", []))
        if "LastEvaluatedKey" not in page:
            return [from_ddb(i) for i in items]
        kwargs["ExclusiveStartKey"] = page["LastEvaluatedKey"]


def scan_all(tbl: Any, **kwargs: Any) -> list[dict]:
    items: list[dict] = []
    while True:
        page = tbl.scan(**kwargs)
        items.extend(page.get("Items", []))
        if "LastEvaluatedKey" not in page:
            return [from_ddb(i) for i in items]
        kwargs["ExclusiveStartKey"] = page["LastEvaluatedKey"]


def batch_get(table_name: str, keys: Iterable[dict]) -> list[dict]:
    """Batch get in chunks of 100, retrying unprocessed keys."""
    keys = list(keys)
    results: list[dict] = []
    for i in range(0, len(keys), 100):
        request = {table_name: {"Keys": keys[i : i + 100]}}
        while request:
            resp = dynamodb().batch_get_item(RequestItems=request)
            results.extend(resp.get("Responses", {}).get(table_name, []))
            request = resp.get("UnprocessedKeys") or {}
    return [from_ddb(r) for r in results]


def transact_write(items: list[dict]) -> None:
    dynamodb().meta.client.transact_write_items(TransactItems=items)


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat(timespec="seconds")


def short_id(prefix: str, nbytes: int = 3) -> str:
    return f"{prefix}_{secrets.token_hex(nbytes)}"


def scan_id_for(dt: datetime) -> str:
    """Sortable scan id: s_<epoch ms>_<rand>."""
    return f"s_{int(dt.timestamp() * 1000):013d}_{secrets.token_hex(2)}"

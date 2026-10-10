"""Atomic counters in the Stats table (UpdateItem ADD)."""
from typing import Iterable, Mapping

from lib import config, db
from lib.pricing import round2

COUNTERS = (
    "scannedKg",
    "recyclableKg",
    "compostableKg",
    "landfillKg",
    "divertedKg",
    "householdPayoutRs",
    "pickerPayoutRs",
    "eprRs",
    "scanCount",
    "pickupCount",
)


def user_scope(user_id: str) -> str:
    return f"user#{user_id}"


def society_scope(society_id: str) -> str:
    return f"society#{society_id}"


def picker_scope(picker_id: str) -> str:
    return f"picker#{picker_id}"


def increment(scope: str, counters: Mapping[str, float]) -> None:
    deltas = {k: v for k, v in counters.items() if k in COUNTERS and v}
    if not deltas:
        return
    names = {f"#c{i}": k for i, k in enumerate(deltas)}
    values = {f":v{i}": db.to_ddb(float(v) if isinstance(v, float) else v) for i, v in enumerate(deltas.values())}
    expr = "ADD " + ", ".join(f"#c{i} :v{i}" for i in range(len(deltas)))
    db.table(config.stats_table()).update_item(
        Key={"scope": scope},
        UpdateExpression=expr,
        ExpressionAttributeNames=names,
        ExpressionAttributeValues=values,
    )


def _normalise(item: Mapping | None) -> dict:
    item = item or {}
    return {k: round2(item.get(k, 0)) if k.endswith(("Kg", "Rs")) else int(item.get(k, 0)) for k in COUNTERS}


def get(scope: str) -> dict:
    item = db.table(config.stats_table()).get_item(Key={"scope": scope}).get("Item")
    return _normalise(db.from_ddb(item))


def get_many(scopes: Iterable[str]) -> dict[str, dict]:
    scopes = list(dict.fromkeys(scopes))
    found = {i["scope"]: i for i in db.batch_get(config.stats_table(), [{"scope": s} for s in scopes])}
    return {s: _normalise(found.get(s)) for s in scopes}

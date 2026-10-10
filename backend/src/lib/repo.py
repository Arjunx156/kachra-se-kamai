"""Repository: all table reads/writes for users, societies, rates, scans and bundles."""
from typing import Optional

from boto3.dynamodb.conditions import Key

from lib import config, db
from lib.http import AppError
from lib.materials import DISPLAY, RECYCLABLE_MATERIALS, Material

# ---------- users ----------


def get_user(user_id: str) -> Optional[dict]:
    item = db.table(config.users_table()).get_item(Key={"userId": user_id}).get("Item")
    return db.from_ddb(item) if item else None


def require_user(user_id: str, role: Optional[str] = None) -> dict:
    user = get_user(user_id)
    if not user:
        raise AppError("USER_NOT_FOUND", "We couldn't find that user. Try re-selecting your role.", 404)
    if role and user.get("role") != role:
        raise AppError("FORBIDDEN", f"This action is only for {role} accounts.", 403)
    return user


def put_user(user: dict) -> None:
    db.table(config.users_table()).put_item(Item=db.to_ddb(user))


# ---------- societies ----------


def list_societies() -> list[dict]:
    return db.scan_all(db.table(config.societies_table()))


def societies_by_id() -> dict[str, dict]:
    return {s["societyId"]: s for s in list_societies()}


def get_society(society_id: str) -> Optional[dict]:
    item = db.table(config.societies_table()).get_item(Key={"societyId": society_id}).get("Item")
    return db.from_ddb(item) if item else None


def put_society(society: dict) -> None:
    db.table(config.societies_table()).put_item(Item=db.to_ddb(society))


# ---------- rates ----------


def load_rates() -> dict[str, float]:
    """Current Rs/kg per recyclable material: table values over DEMO defaults."""
    rates = dict(config.DEMO_RATES)
    for row in db.scan_all(db.table(config.rates_table())):
        rates[row["material"]] = float(row["rsPerKg"])
    return rates


def list_rates() -> list[dict]:
    stored = {r["material"]: r for r in db.scan_all(db.table(config.rates_table()))}
    rows = []
    for m in RECYCLABLE_MATERIALS:
        row = stored.get(m.value, {})
        en, hi = DISPLAY[m]
        rows.append(
            {
                "material": m.value,
                "displayEn": en,
                "displayHi": hi,
                "rsPerKg": float(row.get("rsPerKg", config.DEMO_RATES[m.value])),
                "updatedBy": row.get("updatedBy"),
                "updatedAt": row.get("updatedAt"),
                "isDemoRate": row.get("updatedBy") in (None, "seed"),
            }
        )
    return rows


def put_rate(material: Material, rs_per_kg: float, updated_by: str, updated_at: str) -> dict:
    item = {"material": material.value, "rsPerKg": float(rs_per_kg), "updatedBy": updated_by, "updatedAt": updated_at}
    db.table(config.rates_table()).put_item(Item=db.to_ddb(item))
    return item


# ---------- scans ----------


def put_scan(scan: dict) -> None:
    db.table(config.scans_table()).put_item(Item=db.to_ddb(scan))


def get_scan(user_id: str, scan_id: str) -> Optional[dict]:
    item = db.table(config.scans_table()).get_item(Key={"userId": user_id, "scanId": scan_id}).get("Item")
    return db.from_ddb(item) if item else None


def list_user_scans(user_id: str, limit: Optional[int] = None) -> list[dict]:
    kwargs: dict = {"KeyConditionExpression": Key("userId").eq(user_id), "ScanIndexForward": False}
    tbl = db.table(config.scans_table())
    if limit:
        kwargs["Limit"] = limit
        return [db.from_ddb(i) for i in tbl.query(**kwargs).get("Items", [])]
    return db.query_all(tbl, **kwargs)


def list_scans_by_status(status: str) -> list[dict]:
    return db.query_all(
        db.table(config.scans_table()),
        IndexName="status-index",
        KeyConditionExpression=Key("status").eq(status),
    )


def get_scans(refs: list[dict]) -> list[dict]:
    keys = [{"userId": r["userId"], "scanId": r["scanId"]} for r in refs]
    return db.batch_get(config.scans_table(), keys)


# ---------- bundles ----------


def get_bundle(bundle_id: str) -> Optional[dict]:
    item = db.table(config.bundles_table()).get_item(Key={"bundleId": bundle_id}).get("Item")
    return db.from_ddb(item) if item else None


def require_bundle(bundle_id: str) -> dict:
    bundle = get_bundle(bundle_id)
    if not bundle:
        raise AppError("BUNDLE_NOT_FOUND", "That pickup bundle no longer exists.", 404)
    return bundle


def list_bundles(status: str) -> list[dict]:
    return db.query_all(
        db.table(config.bundles_table()),
        IndexName="status-index",
        KeyConditionExpression=Key("status").eq(status),
        ScanIndexForward=False,
    )

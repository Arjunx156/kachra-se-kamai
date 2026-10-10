"""Bundle lifecycle: build from pending scans, accept by a picker, collect and pay out."""
import logging
from collections import defaultdict
from datetime import datetime
from typing import Optional

from botocore.exceptions import ClientError

from lib import bundling, config, db, pricing, repo, stats
from lib.http import AppError

logger = logging.getLogger()


def _scan_key(ref: dict) -> dict:
    return {"userId": ref["userId"], "scanId": ref["scanId"]}


def build_bundles(now: Optional[datetime] = None) -> list[dict]:
    """Group pending scans into bundles; each bundle + its scan updates is one transaction."""
    now = now or db.now_utc()
    pending = repo.list_scans_by_status("pending")
    groups = bundling.ready_groups(pending, now, config.min_bundle_kg(), config.BUNDLE_MAX_AGE_HOURS)
    rates = repo.load_rates()
    created = []
    for society_id, scans in groups.items():
        ordered = sorted(scans, key=lambda s: s["createdAt"])
        for chunk in bundling.chunks(ordered, config.MAX_SCANS_PER_BUNDLE):
            bundle = bundling.build_bundle(db.short_id("b", 4), society_id, chunk, rates, now)
            if _write_bundle(bundle, chunk):
                created.append(bundle)
    return created


def _write_bundle(bundle: dict, scans: list[dict]) -> bool:
    items = [
        {
            "Put": {
                "TableName": config.bundles_table(),
                "Item": db.to_ddb(bundle),
                "ConditionExpression": "attribute_not_exists(bundleId)",
            }
        }
    ]
    for s in scans:
        items.append(
            {
                "Update": {
                    "TableName": config.scans_table(),
                    "Key": _scan_key(s),
                    "UpdateExpression": "SET #s = :bundled, bundleId = :b",
                    "ConditionExpression": "#s = :pending",
                    "ExpressionAttributeNames": {"#s": "status"},
                    "ExpressionAttributeValues": {":bundled": "bundled", ":pending": "pending", ":b": bundle["bundleId"]},
                }
            }
        )
    try:
        db.transact_write(items)
        return True
    except ClientError as exc:
        if exc.response.get("Error", {}).get("Code") == "TransactionCanceledException":
            logger.warning("bundle_write_skipped society=%s reason=concurrent_update", bundle["societyId"])
            return False
        raise


def accept_bundle(bundle_id: str, picker_id: str, now: Optional[datetime] = None) -> dict:
    repo.require_user(picker_id, role="picker")
    repo.require_bundle(bundle_id)
    try:
        resp = db.table(config.bundles_table()).update_item(
            Key={"bundleId": bundle_id},
            UpdateExpression="SET #s = :accepted, pickerId = :p, acceptedAt = :t",
            ConditionExpression="#s = :open",
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues={":accepted": "accepted", ":open": "open", ":p": picker_id, ":t": db.iso(now or db.now_utc())},
            ReturnValues="ALL_NEW",
        )
    except ClientError as exc:
        if exc.response.get("Error", {}).get("Code") == "ConditionalCheckFailedException":
            raise AppError("BUNDLE_TAKEN", "Another picker already accepted this pickup.", 409) from exc
        raise
    return db.from_ddb(resp["Attributes"])


def collect_bundle(bundle_id: str, picker_id: str, now: Optional[datetime] = None) -> dict:
    """Mark collected, compute final payouts at current rates, credit EPR and update all counters."""
    now = now or db.now_utc()
    repo.require_user(picker_id, role="picker")
    bundle = repo.require_bundle(bundle_id)
    if bundle.get("status") != "accepted" or bundle.get("pickerId") != picker_id:
        raise AppError("BUNDLE_NOT_ACCEPTED", "Accept this pickup before marking it collected.", 409)

    scans = repo.get_scans(bundle["scanRefs"])
    rates = repo.load_rates()
    materials = pricing.material_kg(bundling.recyclable_items(scans))
    value = pricing.recyclable_value(materials, rates)
    kg_by_scan = bundling.recyclable_kg_by_scan(scans)
    picker_rs, shares = pricing.split_payout(value, kg_by_scan)
    epr_by_scan = {f"{s['userId']}|{s['scanId']}": float(s.get("eprRs") or 0) for s in scans}
    household_rs = pricing.round2(sum(shares.values()))
    epr_rs = pricing.round2(sum(epr_by_scan.values()))

    _write_collection(bundle_id, picker_id, scans, shares, epr_by_scan, value, picker_rs, household_rs, epr_rs, now)
    _credit_stats(bundle, picker_id, scans, kg_by_scan, shares, epr_by_scan, picker_rs, household_rs, epr_rs)

    return {
        **bundle,
        "status": "collected",
        "collectedAt": db.iso(now),
        "valueRs": value,
        "pickerRs": picker_rs,
        "householdRs": household_rs,
        "eprRs": epr_rs,
    }


def _write_collection(bundle_id, picker_id, scans, shares, epr_by_scan, value, picker_rs, household_rs, epr_rs, now):
    items = [
        {
            "Update": {
                "TableName": config.bundles_table(),
                "Key": {"bundleId": bundle_id},
                "UpdateExpression": "SET #s = :collected, collectedAt = :t, valueRs = :v, pickerRs = :pr, householdRs = :hr, eprRs = :er",
                "ConditionExpression": "#s = :accepted AND pickerId = :p",
                "ExpressionAttributeNames": {"#s": "status"},
                "ExpressionAttributeValues": db.to_ddb(
                    {
                        ":collected": "collected",
                        ":accepted": "accepted",
                        ":p": picker_id,
                        ":t": db.iso(now),
                        ":v": float(value),
                        ":pr": float(picker_rs),
                        ":hr": float(household_rs),
                        ":er": float(epr_rs),
                    }
                ),
            }
        }
    ]
    for s in scans:
        key = f"{s['userId']}|{s['scanId']}"
        items.append(
            {
                "Update": {
                    "TableName": config.scans_table(),
                    "Key": _scan_key(s),
                    "UpdateExpression": "SET #s = :collected, finalRs = :f, eprCreditedRs = :e, collectedAt = :t",
                    "ExpressionAttributeNames": {"#s": "status"},
                    "ExpressionAttributeValues": db.to_ddb(
                        {":collected": "collected", ":f": float(shares.get(key, 0)), ":e": float(epr_by_scan.get(key, 0)), ":t": db.iso(now)}
                    ),
                }
            }
        )
    try:
        db.transact_write(items)
    except ClientError as exc:
        if exc.response.get("Error", {}).get("Code") == "TransactionCanceledException":
            raise AppError("BUNDLE_NOT_ACCEPTED", "This pickup was already collected.", 409) from exc
        raise


def _credit_stats(bundle, picker_id, scans, kg_by_scan, shares, epr_by_scan, picker_rs, household_rs, epr_rs):
    per_user: dict[str, dict[str, float]] = defaultdict(lambda: {"householdPayoutRs": 0.0, "eprRs": 0.0, "divertedKg": 0.0})
    for s in scans:
        key = f"{s['userId']}|{s['scanId']}"
        u = per_user[s["userId"]]
        u["householdPayoutRs"] += shares.get(key, 0)
        u["eprRs"] += epr_by_scan.get(key, 0)
        u["divertedKg"] += kg_by_scan.get(key, 0)
    for user_id, c in per_user.items():
        stats.increment(stats.user_scope(user_id), {k: pricing.round2(v) for k, v in c.items()})

    diverted = pricing.round2(sum(kg_by_scan.values()))
    shared = {"divertedKg": diverted, "householdPayoutRs": household_rs, "eprRs": epr_rs, "pickupCount": 1}
    stats.increment(stats.society_scope(bundle["societyId"]), shared)
    stats.increment(config.CITY_SCOPE, {**shared, "pickerPayoutRs": picker_rs})
    stats.increment(stats.picker_scope(picker_id), {"pickerPayoutRs": picker_rs, "divertedKg": diverted, "pickupCount": 1})

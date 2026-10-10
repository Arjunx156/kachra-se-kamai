"""Turn a vision analysis into a priced, persisted scan and update counters."""
from datetime import datetime
from typing import Mapping

from lib import config, db, pricing, repo, stats

STATUS_PENDING = "pending"
STATUS_NO_RECYCLABLES = "no_recyclables"


def build_scan(user: Mapping, image_key: str, analysis: Mapping, rates: Mapping[str, float], now: datetime) -> dict:
    items = list(analysis["items"])
    priced = pricing.price_scan(items, rates)
    has_recyclables = priced["totals"]["recyclableKg"] > 0
    return {
        "userId": user["userId"],
        "scanId": db.scan_id_for(now),
        "societyId": user.get("societyId") or "unknown",
        "imageKey": image_key,
        "createdAt": db.iso(now),
        "items": items,
        **priced,
        "segregationScore": int(analysis.get("segregationScore", 0)),
        "tip": analysis.get("tip", ""),
        "status": STATUS_PENDING if has_recyclables else STATUS_NO_RECYCLABLES,
    }


def record_scan(
    user: Mapping, image_key: str, analysis: Mapping, rates: Mapping[str, float], now: datetime, demo: bool = False
) -> dict:
    scan = build_scan(user, image_key, analysis, rates, now)
    if demo:
        scan = {**scan, "demo": True}
    repo.put_scan(scan)
    t = scan["totals"]
    counters = {
        "scannedKg": pricing.round2(t["recyclableKg"] + t["compostableKg"] + t["landfillKg"]),
        "recyclableKg": t["recyclableKg"],
        "compostableKg": t["compostableKg"],
        "landfillKg": t["landfillKg"],
        "scanCount": 1,
    }
    for scope in (config.CITY_SCOPE, stats.society_scope(scan["societyId"]), stats.user_scope(scan["userId"])):
        stats.increment(scope, counters)
    return scan

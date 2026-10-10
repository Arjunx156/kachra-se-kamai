"""Deterministic bundling of pending scans and nearest-neighbour route ordering (spec 10.3)."""
import math
from datetime import datetime, timedelta
from typing import Iterable, Iterator, Mapping, Optional, Sequence, TypeVar

from lib import pricing
from lib.materials import is_recyclable, normalize_material

T = TypeVar("T")
EARTH_RADIUS_KM = 6371.0


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def _recyclable_kg(scan: Mapping) -> float:
    return float((scan.get("totals") or {}).get("recyclableKg") or 0)


def _is_old(scan: Mapping, now: datetime, max_age_hours: float) -> bool:
    created = datetime.fromisoformat(scan["createdAt"])
    return now - created >= timedelta(hours=max_age_hours)


def ready_groups(
    scans: Iterable[Mapping], now: datetime, min_kg: float, max_age_hours: float
) -> dict[str, list[Mapping]]:
    """Group pending scans by society; keep groups that meet the kg threshold or hold an old scan."""
    groups: dict[str, list[Mapping]] = {}
    for scan in scans:
        if _recyclable_kg(scan) <= 0:
            continue
        groups.setdefault(scan["societyId"], []).append(scan)
    return {
        society: group
        for society, group in groups.items()
        if sum(_recyclable_kg(s) for s in group) >= min_kg or any(_is_old(s, now, max_age_hours) for s in group)
    }


def chunks(items: Sequence[T], size: int) -> Iterator[Sequence[T]]:
    for i in range(0, len(items), size):
        yield items[i : i + size]


def recyclable_items(scans: Iterable[Mapping]) -> list[Mapping]:
    return [it for s in scans for it in s.get("items", []) if is_recyclable(it.get("material"))]


def recyclable_kg_by_scan(scans: Iterable[Mapping]) -> dict[str, float]:
    """Recyclable kg per scan, keyed 'userId|scanId' (used for the household payout split)."""
    result = {}
    for s in scans:
        kg = sum(pricing.material_kg(recyclable_items([s])).values())
        result[f"{s['userId']}|{s['scanId']}"] = pricing.round2(kg)
    return result


def build_bundle(bundle_id: str, society_id: str, scans: Sequence[Mapping], rates: Mapping[str, float], now: datetime) -> dict:
    materials = pricing.material_kg(recyclable_items(scans))
    materials = {normalize_material(m).value: kg for m, kg in materials.items() if kg > 0}
    return {
        "bundleId": bundle_id,
        "societyId": society_id,
        "scanRefs": [{"userId": s["userId"], "scanId": s["scanId"]} for s in scans],
        "householdCount": len({s["userId"] for s in scans}),
        "materials": materials,
        "totalKg": pricing.round2(sum(materials.values())),
        "valueRs": pricing.recyclable_value(materials, rates),
        "status": "open",
        "createdAt": now.isoformat(),
    }


def route_order(base: Optional[tuple[float, float]], stops: Sequence[Mapping]) -> tuple[list[dict], float]:
    """Greedy nearest-neighbour ordering from the picker's base. Returns new dicts; inputs are untouched."""
    remaining = [dict(s) for s in stops]
    if not remaining:
        return [], 0.0
    current = base or (remaining[0]["lat"], remaining[0]["lng"])
    ordered: list[dict] = []
    total = 0.0
    while remaining:
        nearest = min(remaining, key=lambda s: haversine_km(current[0], current[1], s["lat"], s["lng"]))
        remaining.remove(nearest)
        dist = round(haversine_km(current[0], current[1], nearest["lat"], nearest["lng"]), 2)
        total += dist
        ordered.append({**nearest, "routeOrder": len(ordered) + 1, "distanceKmFromPrev": dist})
        current = (nearest["lat"], nearest["lng"])
    return ordered, round(total, 2)

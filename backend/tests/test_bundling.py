from datetime import datetime, timedelta, timezone

import pytest

from lib import bundling
from lib.config import DEMO_RATES

NOW = datetime(2026, 10, 10, 18, 0, tzinfo=timezone.utc)


def scan(user, society, kg_by_material, hours_ago=1.0, scan_id=None):
    items = [{"name": m, "material": m, "count": 1, "estWeightKg": kg, "brand": None} for m, kg in kg_by_material.items()]
    recyclable = sum(kg for m, kg in kg_by_material.items() if m not in {"WET_ORGANIC", "SANITARY", "OTHER_LANDFILL"})
    return {
        "userId": user,
        "scanId": scan_id or f"s_{user}_{hours_ago}",
        "societyId": society,
        "createdAt": (NOW - timedelta(hours=hours_ago)).isoformat(),
        "items": items,
        "totals": {"recyclableKg": round(recyclable, 2)},
        "status": "pending",
    }


def test_haversine_known_distance():
    # Connaught Place -> India Gate is roughly 2.3 km
    d = bundling.haversine_km(28.6315, 77.2167, 28.6129, 77.2295)
    assert 2.2 < d < 2.5
    assert bundling.haversine_km(28.6, 77.2, 28.6, 77.2) == 0


def test_group_below_threshold_and_fresh_is_not_ready():
    scans = [scan("u1", "soc_a", {"PET_BOTTLE": 0.5}), scan("u2", "soc_a", {"PAPER": 0.5})]
    assert bundling.ready_groups(scans, NOW, min_kg=1.5, max_age_hours=12) == {}


def test_group_at_threshold_is_ready():
    scans = [scan("u1", "soc_a", {"PET_BOTTLE": 0.75}), scan("u2", "soc_a", {"PAPER": 0.75})]
    groups = bundling.ready_groups(scans, NOW, min_kg=1.5, max_age_hours=12)
    assert list(groups) == ["soc_a"]
    assert len(groups["soc_a"]) == 2


def test_old_scan_makes_small_group_ready():
    scans = [scan("u1", "soc_a", {"PET_BOTTLE": 0.1}, hours_ago=13)]
    assert list(bundling.ready_groups(scans, NOW, min_kg=1.5, max_age_hours=12)) == ["soc_a"]


def test_grouping_is_per_society():
    scans = [
        scan("u1", "soc_a", {"METAL": 1.0}),
        scan("u2", "soc_a", {"PAPER": 1.0}),
        scan("u3", "soc_b", {"PAPER": 1.0}),
        scan("u4", "soc_c", {"PAPER": 0.2}, hours_ago=20),
    ]
    groups = bundling.ready_groups(scans, NOW, min_kg=1.5, max_age_hours=12)
    assert sorted(groups) == ["soc_a", "soc_c"]
    assert {s["userId"] for s in groups["soc_a"]} == {"u1", "u2"}


def test_scans_without_recyclables_are_ignored():
    scans = [scan("u1", "soc_a", {"WET_ORGANIC": 3.0}, hours_ago=30)]
    assert bundling.ready_groups(scans, NOW, min_kg=1.5, max_age_hours=12) == {}


def test_build_bundle_aggregates_recyclable_materials_only():
    scans = [
        scan("u1", "soc_a", {"PET_BOTTLE": 0.2, "WET_ORGANIC": 1.0}),
        scan("u2", "soc_a", {"PET_BOTTLE": 0.3, "METAL": 0.4}),
        scan("u2", "soc_a", {"PAPER": 1.0}, scan_id="s_other"),
    ]
    bundle = bundling.build_bundle("b_1", "soc_a", scans, DEMO_RATES, NOW)
    assert bundle["materials"] == {"PET_BOTTLE": 0.5, "METAL": 0.4, "PAPER": 1.0}
    assert bundle["totalKg"] == 1.9
    assert bundle["valueRs"] == 0.5 * 15 + 0.4 * 25 + 1.0 * 10
    assert bundle["householdCount"] == 2
    assert bundle["status"] == "open"
    assert len(bundle["scanRefs"]) == 3
    assert bundle["scanRefs"][0] == {"userId": "u1", "scanId": scans[0]["scanId"]}


def test_chunks_respect_transaction_limit():
    items = list(range(250))
    chunks = list(bundling.chunks(items, 99))
    assert [len(c) for c in chunks] == [99, 99, 52]


def test_nearest_neighbour_route_order():
    base = (0.0, 0.0)
    stops = [
        {"bundleId": "far", "lat": 0.0, "lng": 0.3},
        {"bundleId": "near", "lat": 0.0, "lng": 0.1},
        {"bundleId": "mid", "lat": 0.0, "lng": 0.2},
    ]
    ordered, total = bundling.route_order(base, stops)
    assert [s["bundleId"] for s in ordered] == ["near", "mid", "far"]
    assert [s["routeOrder"] for s in ordered] == [1, 2, 3]
    assert ordered[0]["distanceKmFromPrev"] == pytest.approx(11.12, abs=0.05)
    assert total == pytest.approx(33.36, abs=0.1)
    # input not mutated
    assert "routeOrder" not in stops[0]


def test_route_order_without_base_or_stops():
    assert bundling.route_order((28.6, 77.2), []) == ([], 0.0)
    ordered, _ = bundling.route_order(None, [{"bundleId": "x", "lat": 1, "lng": 1}])
    assert ordered[0]["routeOrder"] == 1
    assert ordered[0]["distanceKmFromPrev"] == 0.0


def test_scan_kg_by_household():
    scans = [
        scan("u1", "soc_a", {"PET_BOTTLE": 0.2, "WET_ORGANIC": 1.0}, scan_id="s1"),
        scan("u2", "soc_a", {"METAL": 0.4}, scan_id="s2"),
    ]
    assert bundling.recyclable_kg_by_scan(scans) == {"u1|s1": 0.2, "u2|s2": 0.4}

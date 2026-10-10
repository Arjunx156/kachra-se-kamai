"""Society leaderboard ranked by kg diverted from landfill."""
from lib import repo, stats


def compute() -> list[dict]:
    societies = repo.list_societies()
    counters = stats.get_many(stats.society_scope(s["societyId"]) for s in societies)
    rows = []
    for s in societies:
        c = counters[stats.society_scope(s["societyId"])]
        rows.append(
            {
                "societyId": s["societyId"],
                "name": s["name"],
                "area": s.get("area", ""),
                "ward": s.get("ward", ""),
                "divertedKg": c["divertedKg"],
                "scannedKg": c["scannedKg"],
                "householdPayoutRs": c["householdPayoutRs"],
                "eprRs": c["eprRs"],
                "scanCount": c["scanCount"],
                "pickupCount": c["pickupCount"],
            }
        )
    rows.sort(key=lambda r: (-r["divertedKg"], -r["householdPayoutRs"], r["name"]))
    return [{**r, "rank": i + 1} for i, r in enumerate(rows)]

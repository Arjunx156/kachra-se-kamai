"""Data functions behind the Kamai Coach agent's tools. Each reads real DynamoDB data for one user."""
from datetime import datetime, timedelta
from typing import Optional

from lib import db, leaderboard, pricing, repo
from lib.materials import DISPLAY, category_of, normalize_material

MAX_DAYS = 30
MAX_HISTORY = 20


def material_totals(user_id: str, days: int = 7, now: Optional[datetime] = None) -> dict:
    days = max(1, min(MAX_DAYS, int(days)))
    since = db.iso((now or db.now_utc()) - timedelta(days=days))
    scans = [s for s in repo.list_user_scans(user_id) if s.get("createdAt", "") >= since]
    by_material = pricing.material_kg([it for s in scans for it in s.get("items", [])])
    by_category: dict[str, float] = {}
    for code, kg in by_material.items():
        cat = category_of(code)
        by_category[cat] = pricing.round2(by_category.get(cat, 0) + kg)
    return {
        "days": days,
        "scanCount": len(scans),
        "kgByMaterial": {DISPLAY[normalize_material(c)][0]: kg for c, kg in sorted(by_material.items(), key=lambda x: -x[1])},
        "kgByCategory": by_category,
        "brandedPackets": sum(int(s.get("eprPackets", 0)) for s in scans),
    }


def scan_history(user_id: str, limit: int = 10) -> list[dict]:
    limit = max(1, min(MAX_HISTORY, int(limit)))
    return [
        {
            "date": s.get("createdAt", "")[:10],
            "totals": s.get("totals", {}),
            "segregationScore": s.get("segregationScore"),
            "estValueRs": s.get("estValueRs"),
            "status": s.get("status"),
            "tip": s.get("tip"),
        }
        for s in repo.list_user_scans(user_id, limit=limit)
    ]


def rates() -> dict:
    return {DISPLAY[normalize_material(c)][0]: rs for c, rs in repo.load_rates().items()}


def society_rank(user_id: str) -> dict:
    user = repo.get_user(user_id) or {}
    board = leaderboard.compute()
    mine = next((r for r in board if r["societyId"] == user.get("societyId")), None)
    if not mine:
        return {"rank": None, "societies": len(board)}
    leader = board[0]
    return {
        "society": mine["name"],
        "rank": mine["rank"],
        "societies": len(board),
        "societyDivertedKg": mine["divertedKg"],
        "leader": leader["name"],
        "leaderDivertedKg": leader["divertedKg"],
    }

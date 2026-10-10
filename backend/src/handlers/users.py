"""POST /users, GET /me"""
from datetime import timedelta

from lib import db, pricing, repo, stats
from lib.http import AppError, api_handler, body_json, ok, parse, query
from lib.models import CreateUserRequest

WEEK_DAYS = 7


def create_user(event: dict) -> dict:
    req = parse(CreateUserRequest, body_json(event))
    if req.role == "household":
        if not req.societyId or not repo.get_society(req.societyId):
            raise AppError("SOCIETY_NOT_FOUND", "Pick a valid society for a household account.", 400)
    user = {"userId": db.short_id("u", 3), "createdAt": db.iso(db.now_utc()), **req.model_dump(exclude_none=True)}
    repo.put_user(user)
    return ok(user, 201)


def _week_summary(scans: list[dict]) -> dict:
    since = db.iso(db.now_utc() - timedelta(days=WEEK_DAYS))
    week = [s for s in scans if s.get("createdAt", "") >= since]
    sums = {"recyclableKg": 0.0, "compostableKg": 0.0, "landfillKg": 0.0}
    for s in week:
        for k in sums:
            sums[k] += float((s.get("totals") or {}).get(k, 0))
    return {"scans": len(week), **{k: pricing.round2(v) for k, v in sums.items()}}


def me(event: dict) -> dict:
    user_id = query(event).get("userId", "")
    if not user_id:
        raise AppError("BAD_REQUEST", "userId is required.")
    user = repo.require_user(user_id)
    scope = stats.picker_scope(user_id) if user["role"] == "picker" else stats.user_scope(user_id)
    counters = stats.get(scope)
    data: dict = {
        "user": user,
        "stats": counters,
        "wallet": {k: counters[k] for k in ("householdPayoutRs", "eprRs", "divertedKg", "pickerPayoutRs", "pickupCount")},
    }
    if user["role"] == "household":
        scans = repo.list_user_scans(user_id)
        scores = [int(s.get("segregationScore", 0)) for s in scans]
        data["week"] = _week_summary(scans)
        data["avgScore"] = round(sum(scores) / len(scores)) if scores else None
        data["latestScan"] = scans[0] if scans else None
        data["pendingRs"] = pricing.round2(sum(float(s.get("estValueRs", 0)) for s in scans if s.get("status") in ("pending", "bundled")))
        data["society"] = repo.get_society(user.get("societyId", "")) if user.get("societyId") else None
    return ok(data)


lambda_handler = api_handler({"POST /users": create_user, "GET /me": me})

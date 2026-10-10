"""GET /rates, PUT /rates/{material}"""
from lib import db, repo
from lib.http import AppError, api_handler, body_json, ok, parse, path_param
from lib.materials import Material, is_recyclable
from lib.models import RateUpdateRequest


def get_rates(_event: dict) -> dict:
    return ok({"rates": repo.list_rates(), "note": "Demo rates, not market data."})


def put_rate(event: dict) -> dict:
    code = path_param(event, "material").upper()
    if code not in Material.__members__ or not is_recyclable(code):
        raise AppError("BAD_MATERIAL", "Rates can only be set for recyclable materials.", 400)
    req = parse(RateUpdateRequest, body_json(event))
    repo.require_user(req.userId, role="recycler")
    row = repo.put_rate(Material(code), req.rsPerKg, req.userId, db.iso(db.now_utc()))
    return ok(row)


lambda_handler = api_handler({"GET /rates": get_rates, "PUT /rates/{material}": put_rate})

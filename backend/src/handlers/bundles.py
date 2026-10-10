"""POST /bundles/build, GET /bundles, GET /bundles/{id}, POST /bundles/{id}/accept, POST /bundles/{id}/collect"""
from lib import bundle_service, bundling, config, pricing, repo
from lib.http import AppError, api_handler, body_json, ok, parse, path_param, query
from lib.models import PickerRequest

STATUSES = {"open", "accepted", "collected"}


def _decorate(bundle: dict, societies: dict) -> dict:
    s = societies.get(bundle["societyId"], {})
    value = float(bundle.get("valueRs", 0))
    return {
        **bundle,
        "societyName": s.get("name", bundle["societyId"]),
        "area": s.get("area", ""),
        "lat": s.get("lat"),
        "lng": s.get("lng"),
        "pickerShareRs": float(bundle.get("pickerRs", pricing.round2(value * config.PICKER_SHARE))),
    }


def build(_event: dict) -> dict:
    created = bundle_service.build_bundles()
    return ok({"created": len(created), "bundles": created})


def list_bundles(event: dict) -> dict:
    params = query(event)
    status = params.get("status", "open")
    if status not in STATUSES:
        raise AppError("BAD_REQUEST", f"status must be one of {sorted(STATUSES)}.")
    picker_id = params.get("pickerId")
    societies = repo.societies_by_id()
    bundles = [_decorate(b, societies) for b in repo.list_bundles(status)]
    base = None
    if picker_id:
        picker = repo.require_user(picker_id, role="picker")
        if picker.get("lat") is not None and picker.get("lng") is not None:
            base = (float(picker["lat"]), float(picker["lng"]))
        if status != "open":
            bundles = [b for b in bundles if b.get("pickerId") == picker_id]
    routable = [b for b in bundles if b.get("lat") is not None]
    ordered, total_km = bundling.route_order(base, routable) if status != "collected" else (bundles, 0.0)
    return ok({"bundles": ordered, "totalRouteKm": total_km, "base": {"lat": base[0], "lng": base[1]} if base else None})


def get_bundle(event: dict) -> dict:
    bundle = repo.require_bundle(path_param(event, "bundleId"))
    return ok(_decorate(bundle, repo.societies_by_id()))


def accept(event: dict) -> dict:
    req = parse(PickerRequest, body_json(event))
    bundle = bundle_service.accept_bundle(path_param(event, "bundleId"), req.pickerId)
    return ok(_decorate(bundle, repo.societies_by_id()))


def collect(event: dict) -> dict:
    req = parse(PickerRequest, body_json(event))
    result = bundle_service.collect_bundle(path_param(event, "bundleId"), req.pickerId)
    return ok(_decorate(result, repo.societies_by_id()))


lambda_handler = api_handler(
    {
        "POST /bundles/build": build,
        "GET /bundles": list_bundles,
        "GET /bundles/{bundleId}": get_bundle,
        "POST /bundles/{bundleId}/accept": accept,
        "POST /bundles/{bundleId}/collect": collect,
    }
)

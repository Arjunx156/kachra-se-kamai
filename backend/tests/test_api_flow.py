"""End-to-end API flow against mocked DynamoDB/S3 (moto) with Bedrock stubbed."""
from pathlib import Path

import boto3

from conftest import ADMIN_KEY, BUCKET, call
from handlers import admin, bundles, rates, scans, stats, uploads, users
from lib import vision

FIXTURES = Path(__file__).parent / "fixtures"


class FakeBedrock:
    def __init__(self, text):
        self.text = text

    def converse(self, **_kwargs):
        return {"output": {"message": {"content": [{"text": self.text}]}}}


def test_health(aws):
    status, body = call(stats.lambda_handler, "GET /health")
    assert status == 200 and body["data"]["status"] == "ok"


def test_unknown_route_returns_404(aws):
    status, body = call(stats.lambda_handler, "GET /nope")
    assert status == 404 and body["ok"] is False


def test_admin_requires_key(aws):
    status, body = call(admin.lambda_handler, "POST /admin/seed", headers={"x-admin-key": "wrong"})
    assert status == 401 and body["error"]["code"] == "UNAUTHORIZED"


def test_admin_disabled_without_key(aws, monkeypatch):
    monkeypatch.setenv("ADMIN_KEY", "")
    status, body = call(admin.lambda_handler, "POST /admin/reset", headers={"x-admin-key": ""})
    assert status == 503


def test_seed_creates_consistent_demo_world(seeded):
    assert seeded["societies"] == 6
    assert seeded["collectedBundles"] >= 4
    status, me = call(users.lambda_handler, "GET /me", query={"userId": "u_priya"})
    assert status == 200
    wallet = me["data"]["wallet"]
    assert wallet["householdPayoutRs"] > 0
    assert wallet["divertedKg"] > 0
    assert me["data"]["avgScore"] is not None
    assert me["data"]["society"]["name"] == "Shanti Apartments"

    _, city = call(stats.lambda_handler, "GET /stats/city")
    c = city["data"]["counters"]
    assert c["scanCount"] == seeded["scans"]
    assert c["householdPayoutRs"] > 0 and c["pickerPayoutRs"] > 0
    assert 0.5 <= city["data"]["mountain"]["heightFactor"] < 1

    _, board = call(stats.lambda_handler, "GET /leaderboard")
    rows = board["data"]["societies"]
    assert len(rows) == 6
    assert rows[0]["rank"] == 1
    assert rows[0]["divertedKg"] >= rows[-1]["divertedKg"]


def test_reseed_is_idempotent(seeded):
    status, body = call(admin.lambda_handler, "POST /admin/seed", headers={"x-admin-key": ADMIN_KEY})
    assert status == 200
    _, city = call(stats.lambda_handler, "GET /stats/city")
    assert city["data"]["counters"]["scanCount"] == seeded["scans"]


def test_reset_wipes_everything(seeded):
    status, body = call(admin.lambda_handler, "POST /admin/reset", headers={"x-admin-key": ADMIN_KEY})
    assert status == 200
    _, city = call(stats.lambda_handler, "GET /stats/city")
    assert city["data"]["counters"]["scanCount"] == 0


def test_bundle_build_accept_collect_updates_everything(seeded):
    _, before_city = call(stats.lambda_handler, "GET /stats/city")
    _, before_picker = call(users.lambda_handler, "GET /me", query={"userId": "u_ramesh"})

    status, built = call(bundles.lambda_handler, "POST /bundles/build")
    assert status == 200 and built["data"]["created"] >= 2

    status, listed = call(bundles.lambda_handler, "GET /bundles", query={"status": "open", "pickerId": "u_ramesh"})
    assert status == 200
    open_bundles = listed["data"]["bundles"]
    assert [b["routeOrder"] for b in open_bundles] == list(range(1, len(open_bundles) + 1))
    assert listed["data"]["totalRouteKm"] > 0
    first = open_bundles[0]
    assert first["pickerShareRs"] > 0 and first["societyName"]

    bid = first["bundleId"]
    status, accepted = call(bundles.lambda_handler, "POST /bundles/{bundleId}/accept", {"pickerId": "u_ramesh"}, path={"bundleId": bid})
    assert status == 200 and accepted["data"]["status"] == "accepted"

    status, again = call(bundles.lambda_handler, "POST /bundles/{bundleId}/accept", {"pickerId": "u_ramesh"}, path={"bundleId": bid})
    assert status == 409 and again["error"]["code"] == "BUNDLE_TAKEN"

    status, collected = call(bundles.lambda_handler, "POST /bundles/{bundleId}/collect", {"pickerId": "u_ramesh"}, path={"bundleId": bid})
    assert status == 200, collected
    data = collected["data"]
    assert data["status"] == "collected"
    assert round(data["pickerRs"] + data["householdRs"], 2) == data["valueRs"]

    status, again = call(bundles.lambda_handler, "POST /bundles/{bundleId}/collect", {"pickerId": "u_ramesh"}, path={"bundleId": bid})
    assert status == 409

    _, after_city = call(stats.lambda_handler, "GET /stats/city")
    assert after_city["data"]["counters"]["divertedKg"] > before_city["data"]["counters"]["divertedKg"]
    assert after_city["data"]["mountain"]["heightFactor"] <= before_city["data"]["mountain"]["heightFactor"]
    _, after_picker = call(users.lambda_handler, "GET /me", query={"userId": "u_ramesh"})
    gained = after_picker["data"]["wallet"]["pickerPayoutRs"] - before_picker["data"]["wallet"]["pickerPayoutRs"]
    assert round(gained, 2) == data["pickerRs"]

    ref = data["scanRefs"][0]
    _, scan = call(scans.lambda_handler, "GET /scans/{scanId}", query={"userId": ref["userId"]}, path={"scanId": ref["scanId"]})
    assert scan["data"]["status"] == "collected" and "finalRs" in scan["data"]

    _, done = call(bundles.lambda_handler, "GET /bundles", query={"status": "collected", "pickerId": "u_ramesh"})
    assert any(b["bundleId"] == bid for b in done["data"]["bundles"])
    _, detail = call(bundles.lambda_handler, "GET /bundles/{bundleId}", path={"bundleId": bid})
    assert detail["data"]["status"] == "collected"


def test_collect_requires_accept_and_picker_role(seeded):
    call(bundles.lambda_handler, "POST /bundles/build")
    _, listed = call(bundles.lambda_handler, "GET /bundles", query={"status": "open"})
    bid = listed["data"]["bundles"][0]["bundleId"]
    status, body = call(bundles.lambda_handler, "POST /bundles/{bundleId}/collect", {"pickerId": "u_ramesh"}, path={"bundleId": bid})
    assert status == 409 and body["error"]["code"] == "BUNDLE_NOT_ACCEPTED"
    status, body = call(bundles.lambda_handler, "POST /bundles/{bundleId}/accept", {"pickerId": "u_priya"}, path={"bundleId": bid})
    assert status == 403
    status, body = call(bundles.lambda_handler, "POST /bundles/{bundleId}/accept", {"pickerId": "u_ramesh"}, path={"bundleId": "b_missing"})
    assert status == 404
    status, body = call(bundles.lambda_handler, "GET /bundles", query={"status": "weird"})
    assert status == 400


def test_upload_and_scan_flow_with_stubbed_bedrock(seeded, monkeypatch):
    status, up = call(uploads.lambda_handler, "POST /uploads", {"userId": "u_priya", "contentType": "image/jpeg"})
    assert status == 200
    key = up["data"]["imageKey"]
    assert key.startswith("scans/u_priya/") and key.endswith(".jpg")
    assert up["data"]["uploadUrl"].startswith("https://")

    boto3.client("s3", region_name="us-east-1").put_object(Bucket=BUCKET, Key=key, Body=b"\xff\xd8fake", ContentType="image/jpeg")
    monkeypatch.setattr(vision, "_bedrock_client", lambda: FakeBedrock((FIXTURES / "mixed_bin.json").read_text()))

    status, scan = call(scans.lambda_handler, "POST /scans", {"userId": "u_priya", "imageKey": key})
    assert status == 201, scan
    s = scan["data"]
    assert s["status"] == "pending"
    assert s["eprPackets"] == 9 and s["eprRs"] == 4.5
    assert s["estValueRs"] > 0
    assert s["societyName"] == "Shanti Apartments"
    assert s["imageUrl"].startswith("https://")

    _, listing = call(scans.lambda_handler, "GET /scans", query={"userId": "u_priya"})
    assert listing["data"]["scans"][0]["scanId"] == s["scanId"]


def test_scan_errors(seeded, monkeypatch):
    status, body = call(uploads.lambda_handler, "POST /uploads", {"userId": "u_priya", "contentType": "image/gif"})
    assert status == 415
    status, body = call(uploads.lambda_handler, "POST /uploads", {"userId": "u_ramesh", "contentType": "image/png"})
    assert status == 403
    status, body = call(scans.lambda_handler, "POST /scans", {"userId": "u_priya", "imageKey": "scans/u_amit/x.jpg"})
    assert status == 403 and body["error"]["code"] == "BAD_IMAGE_KEY"
    status, body = call(scans.lambda_handler, "POST /scans", {"userId": "u_priya", "imageKey": "scans/u_priya/missing.jpg"})
    assert status == 404 and body["error"]["code"] == "IMAGE_NOT_FOUND"
    status, body = call(scans.lambda_handler, "POST /scans", {"userId": "bad id!", "imageKey": "k"})
    assert status == 400 and body["error"]["code"] == "VALIDATION_ERROR"

    key = "scans/u_priya/desk.jpg"
    boto3.client("s3", region_name="us-east-1").put_object(Bucket=BUCKET, Key=key, Body=b"img", ContentType="image/jpeg")
    monkeypatch.setattr(vision, "_bedrock_client", lambda: FakeBedrock((FIXTURES / "not_a_bin.json").read_text()))
    status, body = call(scans.lambda_handler, "POST /scans", {"userId": "u_priya", "imageKey": key})
    assert status == 422 and body["error"]["code"] == "NOT_A_BIN"

    status, body = call(scans.lambda_handler, "GET /scans/{scanId}", query={"userId": "u_priya"}, path={"scanId": "s_nope"})
    assert status == 404
    status, body = call(scans.lambda_handler, "GET /scans", query={})
    assert status == 400


def test_rate_board_and_rate_change_affects_next_estimate(seeded):
    status, board = call(rates.lambda_handler, "GET /rates")
    assert status == 200
    pet = next(r for r in board["data"]["rates"] if r["material"] == "PET_BOTTLE")
    assert pet["rsPerKg"] == 15 and pet["isDemoRate"] is True
    assert len(board["data"]["rates"]) == 9

    status, _ = call(rates.lambda_handler, "PUT /rates/{material}", {"userId": "u_recycler", "rsPerKg": 20}, path={"material": "PET_BOTTLE"})
    assert status == 200
    _, board = call(rates.lambda_handler, "GET /rates")
    pet = next(r for r in board["data"]["rates"] if r["material"] == "PET_BOTTLE")
    assert pet["rsPerKg"] == 20 and pet["isDemoRate"] is False

    from lib import pricing, repo

    assert pricing.household_estimate([{"material": "PET_BOTTLE", "estWeightKg": 1.0}], repo.load_rates()) == 12.0

    assert call(rates.lambda_handler, "PUT /rates/{material}", {"userId": "u_priya", "rsPerKg": 20}, path={"material": "PET_BOTTLE"})[0] == 403
    assert call(rates.lambda_handler, "PUT /rates/{material}", {"userId": "u_recycler", "rsPerKg": 900}, path={"material": "PET_BOTTLE"})[0] == 400
    assert call(rates.lambda_handler, "PUT /rates/{material}", {"userId": "u_recycler", "rsPerKg": 5}, path={"material": "WET_ORGANIC"})[0] == 400


def test_create_user(seeded):
    status, body = call(users.lambda_handler, "POST /users", {"name": "Test", "role": "household", "societyId": "soc_laxmi"})
    assert status == 201 and body["data"]["userId"].startswith("u_")
    status, body = call(users.lambda_handler, "POST /users", {"name": "Test", "role": "household", "societyId": "soc_none"})
    assert status == 400
    status, body = call(users.lambda_handler, "POST /users", {"name": "P", "role": "picker", "lat": 28.6, "lng": 77.2})
    assert status == 201
    status, body = call(users.lambda_handler, "POST /users", {"name": "", "role": "admin"})
    assert status == 400
    status, body = call(users.lambda_handler, "GET /me", query={"userId": "u_ghost"})
    assert status == 404


def test_bad_json_body(aws):
    resp = users.lambda_handler({"routeKey": "POST /users", "body": "{oops"}, None)
    assert resp["statusCode"] == 400

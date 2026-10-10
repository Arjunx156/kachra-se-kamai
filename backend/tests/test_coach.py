from conftest import call
from handlers import coach
from lib import coach_tools


def test_coach_tools_read_real_user_data(seeded):
    totals = coach_tools.material_totals("u_priya", days=7)
    assert totals["days"] == 7
    assert totals["scanCount"] > 0
    assert sum(totals["kgByCategory"].values()) > 0

    history = coach_tools.scan_history("u_priya", limit=3)
    assert 0 < len(history) <= 3
    assert {"date", "totals", "segregationScore"} <= set(history[0])

    rates = coach_tools.rates()
    assert rates["PET bottles"] == 15

    rank = coach_tools.society_rank("u_priya")
    assert rank["society"] == "Shanti Apartments"
    assert 1 <= rank["rank"] <= rank["societies"]


def test_coach_tools_clamp_arguments(seeded):
    assert coach_tools.material_totals("u_priya", days=999)["days"] == 30
    assert len(coach_tools.scan_history("u_priya", limit=999)) <= 20
    assert coach_tools.society_rank("u_ghost") == {"rank": None, "societies": 6}


def test_coach_onboarding_without_model_for_new_user(seeded):
    status, body = call(coach.lambda_handler, "POST /users", {})
    assert status == 404
    from handlers import users

    _, created = call(users.lambda_handler, "POST /users", {"name": "New", "role": "household", "societyId": "soc_laxmi"})
    uid = created["data"]["userId"]
    status, body = call(coach.lambda_handler, "POST /coach", {"userId": uid, "language": "hi"})
    assert status == 200
    assert body["data"]["onboarding"] is True
    assert body["data"]["toolsCalled"] == []
    assert body["data"]["plan"].startswith("Swagat")


def test_coach_runs_agent_and_reports_tool_trace(seeded, monkeypatch):
    monkeypatch.setattr(coach, "run_agent", lambda uid, lang: ("1. Do X", ["get_material_totals", "get_rates", "get_rates"]))
    status, body = call(coach.lambda_handler, "POST /coach", {"userId": "u_priya", "language": "en"})
    assert status == 200
    assert body["data"]["toolsCalled"] == ["get_material_totals", "get_rates"]
    assert body["data"]["checked"] == ["your last 7 days", "current rates"]


def test_coach_failure_is_friendly(seeded, monkeypatch):
    def boom(uid, lang):
        raise RuntimeError("AccessDeniedException")

    monkeypatch.setattr(coach, "run_agent", boom)
    status, body = call(coach.lambda_handler, "POST /coach", {"userId": "u_priya"})
    assert status == 503 and body["error"]["code"] == "COACH_UNAVAILABLE"


def test_coach_tools_are_bound_to_user(seeded):
    calls: list[str] = []
    tools = coach._build_tools("u_priya", calls)
    assert [t.tool_name for t in tools] == ["get_material_totals", "get_scan_history", "get_rates", "get_society_rank"]

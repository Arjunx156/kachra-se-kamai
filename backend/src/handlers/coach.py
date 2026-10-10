"""POST /coach -> weekly plan from the "Kamai Coach" Strands agent (Amazon Bedrock).

The agent's tools are bound to the requesting user, so the model can only read that household's data.
"""
import logging
from typing import Any, Callable

from lib import coach_tools, config, repo
from lib.http import AppError, api_handler, body_json, ok, parse
from lib.models import CoachRequest

logger = logging.getLogger()

MIN_SCANS = 2
TEMPERATURE = 0.3

SYSTEM_PROMPT = """You are "Kamai Coach", a friendly, practical waste coach for Delhi households.
Use your tools to look at this household's real data before answering. Never invent numbers; only use figures returned by tools.
Write a weekly plan with exactly 3 actions. For each action give: what to do, why (citing their own data), and the expected impact in kg diverted and Rs earned per week, computed from tool data and current rates.
Keep it under 150 words. Respond in {language}."""

LANGUAGES = {"en": "English", "hi": "simple Hinglish (Hindi written in Latin script, mixed with English)"}

TOOL_LABELS = {
    "get_material_totals": "your last 7 days",
    "get_scan_history": "your recent scans",
    "get_rates": "current rates",
    "get_society_rank": "society rank",
}

ONBOARDING = {
    "en": "Welcome! Snap your bin at least twice this week so I can see your real waste mix. Then I'll write you a 3-step plan to earn more and send less to the landfill.",
    "hi": "Swagat hai! Is hafte kam se kam do baar apne bin ki photo lijiye, taaki main aapka asli kachra dekh sakoon. Phir main aapke liye 3 step ka plan banaunga: zyada kamai, kam landfill.",
}


def _build_tools(user_id: str, calls: list[str]) -> list[Callable[..., Any]]:
    from strands import tool

    @tool
    def get_material_totals(days: int = 7) -> dict:
        """Kilograms of waste this household threw away per material and per category (recyclable, compostable, landfill) over the last N days.

        Args:
            days: How many days to look back (1-30). Default 7.
        """
        calls.append("get_material_totals")
        return coach_tools.material_totals(user_id, days)

    @tool
    def get_scan_history(limit: int = 10) -> list:
        """This household's most recent bin scans: date, kg totals, segregation score, estimated Rs value, status and the AI tip.

        Args:
            limit: Number of scans to return (1-20). Default 10.
        """
        calls.append("get_scan_history")
        return coach_tools.scan_history(user_id, limit)

    @tool
    def get_rates() -> dict:
        """Current recycler buy rates in Rs per kg for each recyclable material (demo rates). Households receive 60% of value."""
        calls.append("get_rates")
        return coach_tools.rates()

    @tool
    def get_society_rank() -> dict:
        """This household's society position on the city leaderboard by kg diverted from landfill."""
        calls.append("get_society_rank")
        return coach_tools.society_rank(user_id)

    return [get_material_totals, get_scan_history, get_rates, get_society_rank]


def run_agent(user_id: str, language: str) -> tuple[str, list[str]]:
    from strands import Agent
    from strands.models import BedrockModel

    calls: list[str] = []
    model = BedrockModel(model_id=config.coach_model_id(), region_name=config.aws_region(), temperature=TEMPERATURE)
    agent = Agent(
        model=model,
        tools=_build_tools(user_id, calls),
        system_prompt=SYSTEM_PROMPT.format(language=LANGUAGES[language]),
        callback_handler=None,
    )
    result = agent("Write my weekly plan.")
    return str(result).strip(), calls


def coach(event: dict) -> dict:
    req = parse(CoachRequest, body_json(event))
    repo.require_user(req.userId, role="household")
    if len(repo.list_user_scans(req.userId, limit=MIN_SCANS)) < MIN_SCANS:
        return ok({"plan": ONBOARDING[req.language], "toolsCalled": [], "checked": [], "onboarding": True, "language": req.language})
    try:
        plan, calls = run_agent(req.userId, req.language)
    except AppError:
        raise
    except Exception as exc:  # noqa: BLE001 - surface a friendly error; details in logs
        logger.exception("coach_agent_failed user=%s", req.userId)
        raise AppError("COACH_UNAVAILABLE", "The coach is taking a break. Please try again in a minute.", 503) from exc
    tools = list(dict.fromkeys(calls))
    return ok(
        {
            "plan": plan,
            "toolsCalled": tools,
            "checked": [TOOL_LABELS[t] for t in tools if t in TOOL_LABELS],
            "onboarding": False,
            "language": req.language,
            "model": config.coach_model_id(),
        }
    )


lambda_handler = api_handler({"POST /coach": coach})

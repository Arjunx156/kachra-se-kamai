"""GET /health, GET /stats/city, GET /leaderboard"""
from lib import config, db, leaderboard, pricing, stats
from lib.http import api_handler, ok


def health(_event: dict) -> dict:
    return ok({"status": "ok", "service": "kachra-se-kamai", "time": db.iso(db.now_utc())})


def city(_event: dict) -> dict:
    counters = stats.get(config.CITY_SCOPE)
    target = config.target_kg()
    return ok(
        {
            "counters": counters,
            "mountain": {
                "divertedKg": counters["divertedKg"],
                "targetKg": target,
                "minFactor": config.MOUNTAIN_MIN_FACTOR,
                "heightFactor": round(pricing.mountain_factor(counters["divertedKg"], target), 4),
                "illustrative": True,
            },
            "time": db.iso(db.now_utc()),
        }
    )


def board(_event: dict) -> dict:
    return ok({"societies": leaderboard.compute()})


lambda_handler = api_handler({"GET /health": health, "GET /stats/city": city, "GET /leaderboard": board})

"""Demo data: societies, users, DEMO rates and ~40 historical scans (no Bedrock calls).

All people and society names are fictional. Neighbourhood names are real Delhi areas with
approximate public coordinates. Every seeded record carries demo=True.
"""
import random
from datetime import datetime, timedelta

from lib import bundle_service, config, db, repo, scan_service
from lib.materials import Material

SEED = 2026

# (societyId, society name, area/ward, lat, lng) -- coordinates are approximate neighbourhood centres.
SOCIETIES = [
    ("soc_mayur", "Shanti Apartments", "Mayur Vihar Ph-1", 28.6080, 77.2930),
    ("soc_laxmi", "Gulmohar Residency", "Laxmi Nagar", 28.6304, 77.2773),
    ("soc_patpar", "Navkunj Society", "Patparganj", 28.6250, 77.3000),
    ("soc_lajpat", "Ashoka Enclave", "Lajpat Nagar", 28.5677, 77.2433),
    ("soc_rohini", "Neelkanth Apartments", "Rohini Sec-9", 28.7170, 77.1130),
    ("soc_dwarka", "Sunrise CGHS", "Dwarka Sec-10", 28.5815, 77.0590),
]

# Fixed demo users used by the frontend role switcher.
DEMO_HOUSEHOLD = "u_priya"
DEMO_PICKER = "u_ramesh"
DEMO_RECYCLER = "u_recycler"
DEMO_CITY = "u_city"

HOUSEHOLDS = [
    (DEMO_HOUSEHOLD, "Priya", "soc_mayur"),
    ("u_amit", "Amit", "soc_mayur"),
    ("u_deepak", "Deepak", "soc_mayur"),
    ("u_sunita", "Sunita", "soc_laxmi"),
    ("u_rahul", "Rahul", "soc_laxmi"),
    ("u_joseph", "Joseph", "soc_patpar"),
    ("u_kavita", "Kavita", "soc_patpar"),
    ("u_neha", "Neha", "soc_lajpat"),
    ("u_farah", "Farah", "soc_rohini"),
    ("u_vikram", "Vikram", "soc_dwarka"),
]

OTHER_USERS = [
    {"userId": DEMO_PICKER, "name": "Ramesh", "role": "picker", "lat": 28.6235, "lng": 77.3080},
    {"userId": DEMO_RECYCLER, "name": "Green Loop Recyclers (demo)", "role": "recycler"},
    {"userId": DEMO_CITY, "name": "City view", "role": "city"},
]

M = Material
# Typical bin mixes: (name, material, count, kg, brand). Weights follow the vision prompt's typical ranges.
TEMPLATES = [
    {
        "score": 35,
        "tip": "Keep kitchen waste in a separate bin so plastics stay clean and sellable.",
        "items": [
            ("water bottles", M.PET_BOTTLE, 2, 0.06, "Bisleri"),
            ("chips packets", M.MULTILAYER_PACKET, 3, 0.024, "Lay's"),
            ("milk pouches", M.MILK_POUCH, 2, 0.01, "Amul"),
            ("vegetable peels and leftovers", M.WET_ORGANIC, 1, 0.8, None),
            ("newspaper", M.PAPER, 6, 0.12, None),
        ],
    },
    {
        "score": 85,
        "tip": "Great segregation. Flatten cardboard boxes so more fits in one pickup.",
        "items": [
            ("delivery boxes", M.CARDBOARD, 2, 0.4, None),
            ("cold drink bottles", M.PET_BOTTLE, 4, 0.12, None),
            ("aluminium cans", M.METAL, 2, 0.03, None),
            ("paper bags", M.PAPER, 3, 0.15, None),
        ],
    },
    {
        "score": 70,
        "tip": "Rinse milk pouches before drying them; clean pouches fetch a better rate.",
        "items": [
            ("old newspapers", M.PAPER, 30, 0.6, None),
            ("milk pouches", M.MILK_POUCH, 7, 0.035, "Mother Dairy"),
            ("plastic tub", M.HARD_PLASTIC, 1, 0.05, None),
        ],
    },
    {
        "score": 20,
        "tip": "Wrap sanitary waste separately and keep it out of the dry waste bag.",
        "items": [
            ("food scraps", M.WET_ORGANIC, 1, 1.1, None),
            ("sanitary waste", M.SANITARY, 1, 0.15, None),
            ("snack packets", M.MULTILAYER_PACKET, 2, 0.016, "Haldiram's"),
            ("broken plastic container", M.HARD_PLASTIC, 1, 0.08, None),
        ],
    },
    {
        "score": 60,
        "tip": "Store old batteries in a separate jar; they need safe handling.",
        "items": [
            ("used batteries", M.E_WASTE, 4, 0.1, None),
            ("old charger cable", M.E_WASTE, 1, 0.08, None),
            ("shoe box", M.CARDBOARD, 1, 0.25, None),
            ("tea leaves and peels", M.WET_ORGANIC, 1, 0.4, None),
        ],
    },
    {
        "score": 55,
        "tip": "Keep glass jars whole and separate so they don't injure the picker.",
        "items": [
            ("pickle jar", M.GLASS, 1, 0.3, None),
            ("food tins", M.METAL, 2, 0.1, None),
            ("water bottles", M.PET_BOTTLE, 2, 0.06, "Kinley"),
            ("kitchen waste", M.WET_ORGANIC, 1, 0.5, None),
        ],
    },
]

# (userId, hours ago) for recent pending scans that the demo bundles live.
RECENT_SCANS = [
    ("u_sunita", 5), ("u_rahul", 3), ("u_sunita", 1.5),
    ("u_joseph", 4), ("u_kavita", 2),
    ("u_vikram", 6), ("u_vikram", 2.5),
    ("u_farah", 1),
    ("u_neha", 0.7),
    ("u_amit", 2),
]
HISTORICAL_SCAN_COUNT = 30
# Recent scans are dry-waste bags so that some societies cross MIN_BUNDLE_KG and others don't.
DRY_BAG_TEMPLATES = [TEMPLATES[1], TEMPLATES[2]]
RECENT_SCALE = (1.15, 1.5)


def _analysis(rng: random.Random, template: dict, scale_range: tuple[float, float] = (0.75, 1.35)) -> dict:
    scale = rng.uniform(*scale_range)
    items = [
        {"name": n, "material": m.value, "count": c, "estWeightKg": round(max(0.005, kg * scale), 3), "brand": b}
        for (n, m, c, kg, b) in template["items"]
    ]
    score = max(0, min(100, template["score"] + rng.randint(-8, 8)))
    return {"items": items, "segregationScore": score, "tip": template["tip"]}


def _put_reference_data(now_iso: str) -> None:
    for sid, name, area, lat, lng in SOCIETIES:
        repo.put_society({"societyId": sid, "name": name, "area": area, "ward": area, "lat": lat, "lng": lng, "demo": True})
    for uid, name, sid in HOUSEHOLDS:
        repo.put_user({"userId": uid, "name": name, "role": "household", "societyId": sid, "language": "en", "createdAt": now_iso, "demo": True})
    for u in OTHER_USERS:
        repo.put_user({**u, "language": "hi" if u["role"] == "picker" else "en", "createdAt": now_iso, "demo": True})
    for material, rs in config.DEMO_RATES.items():
        repo.put_rate(Material(material), rs, "seed", now_iso)


def run(now: datetime | None = None) -> dict:
    now = now or db.now_utc()
    rng = random.Random(SEED)
    _put_reference_data(db.iso(now))
    users = {uid: {"userId": uid, "societyId": sid} for uid, _, sid in HOUSEHOLDS}
    rates = repo.load_rates()

    # Historical scans across the last 7 days (Priya gets more so her wallet has history).
    weighted = [DEMO_HOUSEHOLD] * 4 + [uid for uid, _, _ in HOUSEHOLDS]
    for _ in range(HISTORICAL_SCAN_COUNT):
        uid = rng.choice(weighted)
        when = now - timedelta(hours=rng.uniform(14, 7 * 24))
        scan_service.record_scan(users[uid], None, _analysis(rng, rng.choice(TEMPLATES)), rates, when, demo=True)

    # Bundle and collect the historical scans (all older than 12 h) through the real code path.
    bundles = bundle_service.build_bundles(now)
    for b in bundles:
        bundle_service.accept_bundle(b["bundleId"], DEMO_PICKER, now)
        bundle_service.collect_bundle(b["bundleId"], DEMO_PICKER, now)

    # Fresh pending scans, left for the live demo's "Refresh bundles".
    for uid, hours in RECENT_SCANS:
        analysis = _analysis(rng, rng.choice(DRY_BAG_TEMPLATES), RECENT_SCALE)
        scan_service.record_scan(users[uid], None, analysis, rates, now - timedelta(hours=hours), demo=True)

    return {
        "societies": len(SOCIETIES),
        "users": len(HOUSEHOLDS) + len(OTHER_USERS),
        "scans": HISTORICAL_SCAN_COUNT + len(RECENT_SCANS),
        "collectedBundles": len(bundles),
        "demoUsers": {"household": DEMO_HOUSEHOLD, "picker": DEMO_PICKER, "recycler": DEMO_RECYCLER, "city": DEMO_CITY},
    }


def reset() -> dict:
    """Delete every item in every table. This deployment holds demo data only."""
    deleted = {}
    for name, keys in (
        (config.users_table(), ["userId"]),
        (config.societies_table(), ["societyId"]),
        (config.scans_table(), ["userId", "scanId"]),
        (config.bundles_table(), ["bundleId"]),
        (config.rates_table(), ["material"]),
        (config.stats_table(), ["scope"]),
    ):
        tbl = db.table(name)
        projection = ", ".join(f"#k{i}" for i in range(len(keys)))
        names = {f"#k{i}": k for i, k in enumerate(keys)}
        rows = db.scan_all(tbl, ProjectionExpression=projection, ExpressionAttributeNames=names)
        with tbl.batch_writer() as batch:
            for row in rows:
                batch.delete_item(Key={k: row[k] for k in keys})
        deleted[name] = len(rows)
    return {"deleted": deleted}

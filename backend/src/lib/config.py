"""Environment configuration and DEMO constants.

Every value marked DEMO is a placeholder chosen for the hackathon demo,
NOT market data. Replace with verified figures before any real use.
"""
import os


def env(name: str, default: str) -> str:
    return os.environ.get(name, default)


def users_table() -> str:
    return env("USERS_TABLE", "Users")


def societies_table() -> str:
    return env("SOCIETIES_TABLE", "Societies")


def scans_table() -> str:
    return env("SCANS_TABLE", "Scans")


def bundles_table() -> str:
    return env("BUNDLES_TABLE", "Bundles")


def rates_table() -> str:
    return env("RATES_TABLE", "Rates")


def stats_table() -> str:
    return env("STATS_TABLE", "Stats")


def photo_bucket() -> str:
    return env("PHOTO_BUCKET", "kachra-photos-local")


def model_id() -> str:
    return env("MODEL_ID", "us.amazon.nova-lite-v1:0")


def coach_model_id() -> str:
    return env("COACH_MODEL_ID", model_id())


def aws_region() -> str:
    return env("AWS_REGION", "us-east-1")


def admin_key() -> str:
    return env("ADMIN_KEY", "")


def min_bundle_kg() -> float:
    # DEMO: minimum recyclable kg in a society before a pickup bundle is created.
    return float(env("MIN_BUNDLE_KG", "1.5"))


def target_kg() -> float:
    # DEMO: kg diverted at which the illustrative mountain reaches its minimum height.
    return float(env("TARGET_KG", "100"))


# DEMO rates (Rs/kg). NOT market data. Seeded into the Rates table and editable by the recycler.
DEMO_RATES: dict[str, float] = {
    "PET_BOTTLE": 15,
    "HARD_PLASTIC": 10,
    "MILK_POUCH": 8,
    "MULTILAYER_PACKET": 2,
    "PAPER": 10,
    "CARDBOARD": 8,
    "METAL": 25,
    "GLASS": 2,
    "E_WASTE": 20,
}

# DEMO payout split.
PICKER_SHARE = 0.40
HOUSEHOLD_SHARE = 0.60

# DEMO simulated EPR partner reward.
EPR_RS_PER_PACKET = 0.50
EPR_CAP_PER_SCAN_RS = 10.0

BUNDLE_MAX_AGE_HOURS = 12
MAX_TXN_ITEMS = 100
MAX_SCANS_PER_BUNDLE = MAX_TXN_ITEMS - 1  # one slot is the bundle itself

MAX_IMAGE_BYTES = 5 * 1024 * 1024
UPLOAD_URL_EXPIRY_S = 300
IMAGE_VIEW_URL_EXPIRY_S = 3600
ALLOWED_UPLOAD_TYPES = {"image/jpeg": "jpg", "image/png": "png"}

RATE_MIN_RS = 0
RATE_MAX_RS = 500

MOUNTAIN_MIN_FACTOR = 0.5
CITY_SCOPE = "city#delhi"

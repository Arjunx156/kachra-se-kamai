"""Material codes, display names and waste categories (spec section 6)."""
from enum import Enum


class Material(str, Enum):
    PET_BOTTLE = "PET_BOTTLE"
    HARD_PLASTIC = "HARD_PLASTIC"
    MILK_POUCH = "MILK_POUCH"
    MULTILAYER_PACKET = "MULTILAYER_PACKET"
    PAPER = "PAPER"
    CARDBOARD = "CARDBOARD"
    METAL = "METAL"
    GLASS = "GLASS"
    E_WASTE = "E_WASTE"
    WET_ORGANIC = "WET_ORGANIC"
    SANITARY = "SANITARY"
    OTHER_LANDFILL = "OTHER_LANDFILL"


RECYCLABLE = "recyclable"
COMPOSTABLE = "compostable"
LANDFILL = "landfill"

CATEGORY: dict[Material, str] = {
    Material.PET_BOTTLE: RECYCLABLE,
    Material.HARD_PLASTIC: RECYCLABLE,
    Material.MILK_POUCH: RECYCLABLE,
    Material.MULTILAYER_PACKET: RECYCLABLE,
    Material.PAPER: RECYCLABLE,
    Material.CARDBOARD: RECYCLABLE,
    Material.METAL: RECYCLABLE,
    Material.GLASS: RECYCLABLE,
    Material.E_WASTE: RECYCLABLE,
    Material.WET_ORGANIC: COMPOSTABLE,
    Material.SANITARY: LANDFILL,
    Material.OTHER_LANDFILL: LANDFILL,
}

DISPLAY: dict[Material, tuple[str, str]] = {
    Material.PET_BOTTLE: ("PET bottles", "प्लास्टिक बोतल"),
    Material.HARD_PLASTIC: ("Hard plastic", "सख्त प्लास्टिक"),
    Material.MILK_POUCH: ("Milk pouches", "दूध की थैली"),
    Material.MULTILAYER_PACKET: ("Chips / snack packets", "चिप्स के पैकेट"),
    Material.PAPER: ("Paper / newspaper", "कागज़"),
    Material.CARDBOARD: ("Cardboard", "गत्ता"),
    Material.METAL: ("Metal cans", "धातु"),
    Material.GLASS: ("Glass", "कांच"),
    Material.E_WASTE: ("E-waste", "ई-कचरा"),
    Material.WET_ORGANIC: ("Wet / kitchen waste", "गीला कचरा"),
    Material.SANITARY: ("Sanitary waste", "सैनिटरी कचरा"),
    Material.OTHER_LANDFILL: ("Other", "अन्य"),
}

# Branded plastic packaging that earns the simulated EPR reward.
EPR_MATERIALS = frozenset({Material.MULTILAYER_PACKET, Material.MILK_POUCH, Material.PET_BOTTLE})

RECYCLABLE_MATERIALS = tuple(m for m, c in CATEGORY.items() if c == RECYCLABLE)


def normalize_material(value: object) -> Material:
    """Map any model output to a known material; unknown values become OTHER_LANDFILL."""
    if isinstance(value, Material):
        return value
    code = str(value or "").strip().upper().replace("-", "_").replace(" ", "_")
    try:
        return Material(code)
    except ValueError:
        return Material.OTHER_LANDFILL


def category_of(material: object) -> str:
    return CATEGORY[normalize_material(material)]


def is_recyclable(material: object) -> bool:
    return category_of(material) == RECYCLABLE

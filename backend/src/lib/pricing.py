"""Deterministic pricing, payout split and EPR rewards (spec section 9).

The LLM never computes money. Every rupee figure in the system comes from here.
"""
from decimal import ROUND_HALF_UP, Decimal
from typing import Iterable, Mapping

from lib import config
from lib.materials import COMPOSTABLE, EPR_MATERIALS, LANDFILL, RECYCLABLE, category_of, normalize_material

_CENT = Decimal("0.01")


def _dec(value: float | int | Decimal) -> Decimal:
    return value if isinstance(value, Decimal) else Decimal(str(value))


def round2(value: float | int | Decimal) -> float:
    """Round half-up to 2 decimals, avoiding binary float artefacts."""
    return float(_dec(value).quantize(_CENT, rounding=ROUND_HALF_UP))


def material_kg(items: Iterable[Mapping]) -> dict[str, float]:
    """Total kg per material code across item groups."""
    totals: dict[str, Decimal] = {}
    for it in items:
        code = normalize_material(it.get("material")).value
        totals[code] = totals.get(code, Decimal(0)) + _dec(it.get("estWeightKg") or 0)
    return {code: round2(kg) for code, kg in totals.items()}


def category_totals(items: Iterable[Mapping]) -> dict[str, float]:
    sums = {RECYCLABLE: Decimal(0), COMPOSTABLE: Decimal(0), LANDFILL: Decimal(0)}
    for it in items:
        sums[category_of(it.get("material"))] += _dec(it.get("estWeightKg") or 0)
    return {
        "recyclableKg": round2(sums[RECYCLABLE]),
        "compostableKg": round2(sums[COMPOSTABLE]),
        "landfillKg": round2(sums[LANDFILL]),
    }


def recyclable_value(kg_by_material: Mapping[str, float], rates: Mapping[str, float]) -> float:
    """Sum of kg x Rs/kg over recyclable materials only. Missing rates count as 0."""
    total = Decimal(0)
    for code, kg in kg_by_material.items():
        if category_of(code) != RECYCLABLE:
            continue
        total += _dec(kg) * _dec(rates.get(code, 0))
    return round2(total)


def household_estimate(items: Iterable[Mapping], rates: Mapping[str, float]) -> float:
    """Scan-time estimate: the household's share of its own recyclables at current rates."""
    value = recyclable_value(material_kg(items), rates)
    return round2(_dec(value) * _dec(config.HOUSEHOLD_SHARE))


def epr_packets(items: Iterable[Mapping]) -> int:
    """Branded plastic packets eligible for the simulated EPR reward."""
    return sum(
        int(it.get("count") or 1)
        for it in items
        if it.get("brand") and normalize_material(it.get("material")) in EPR_MATERIALS
    )


def epr_reward(packets: int) -> float:
    reward = _dec(packets) * _dec(config.EPR_RS_PER_PACKET)
    return round2(min(reward, _dec(config.EPR_CAP_PER_SCAN_RS)))


def price_scan(items: list[Mapping], rates: Mapping[str, float]) -> dict:
    packets = epr_packets(items)
    return {
        "totals": category_totals(items),
        "estValueRs": household_estimate(items, rates),
        "eprPackets": packets,
        "eprRs": epr_reward(packets),
    }


def split_payout(bundle_value_rs: float, kg_by_household: Mapping[str, float]) -> tuple[float, dict[str, float]]:
    """Split a bundle's value: households 60% (pro rata by recyclable kg), picker 40%.

    Household shares are rounded to 2 decimals; any rounding remainder goes to the picker
    so the split always sums exactly to the bundle value.
    """
    value = _dec(round2(bundle_value_rs))
    total_kg = sum((_dec(kg) for kg in kg_by_household.values()), Decimal(0))
    pool = value * _dec(config.HOUSEHOLD_SHARE)
    shares: dict[str, float] = {}
    paid = Decimal(0)
    for key, kg in kg_by_household.items():
        share = Decimal(0) if total_kg <= 0 else (pool * _dec(kg) / total_kg).quantize(_CENT, rounding=ROUND_HALF_UP)
        shares[key] = float(share)
        paid += share
    return float(value - paid), shares


def mountain_factor(diverted_kg: float, target_kg: float) -> float:
    """Illustrative mountain height factor: 1 -> 0.5 as diverted kg approaches target."""
    if target_kg <= 0:
        return 1.0
    return max(config.MOUNTAIN_MIN_FACTOR, 1 - float(diverted_kg) / float(target_kg))

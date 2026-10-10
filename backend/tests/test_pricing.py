from decimal import Decimal

import pytest

from lib import pricing
from lib.config import DEMO_RATES


def item(material, kg, count=1, brand=None):
    return {"name": material.lower(), "material": material, "count": count, "estWeightKg": kg, "brand": brand}


def test_single_material_value_and_household_estimate():
    items = [item("PET_BOTTLE", 0.2)]
    kg = pricing.material_kg(items)
    assert kg == {"PET_BOTTLE": 0.2}
    assert pricing.recyclable_value(kg, DEMO_RATES) == 3.0  # 0.2 * 15
    assert pricing.household_estimate(items, DEMO_RATES) == 1.8  # 60%


def test_mixed_materials_only_recyclables_are_valued():
    items = [
        item("PET_BOTTLE", 0.1),
        item("METAL", 0.2),
        item("PAPER", 0.5),
        item("WET_ORGANIC", 1.5),
        item("SANITARY", 0.3),
    ]
    kg = pricing.material_kg(items)
    # 0.1*15 + 0.2*25 + 0.5*10 = 1.5 + 5 + 5 = 11.5
    assert pricing.recyclable_value(kg, DEMO_RATES) == 11.5
    assert pricing.category_totals(items) == {"recyclableKg": 0.8, "compostableKg": 1.5, "landfillKg": 0.3}


def test_zero_recyclables_values_zero():
    items = [item("WET_ORGANIC", 2.0), item("OTHER_LANDFILL", 0.4)]
    assert pricing.household_estimate(items, DEMO_RATES) == 0.0
    assert pricing.category_totals(items)["recyclableKg"] == 0.0


def test_unknown_material_counted_as_landfill():
    items = [item("SPACESHIP", 1.0)]
    assert pricing.category_totals(items) == {"recyclableKg": 0.0, "compostableKg": 0.0, "landfillKg": 1.0}


def test_missing_rate_treated_as_zero():
    assert pricing.recyclable_value({"PET_BOTTLE": 1.0}, {}) == 0.0


def test_rounding_half_up_to_two_decimals():
    assert pricing.round2(0.125) == 0.13
    assert pricing.round2(2.675) == 2.68  # float 2.675 is 2.67499..; we round via str -> Decimal
    # kg is rounded first (0.333 -> 0.33); 0.33 * 10 = 3.30 -> 60% = 1.98
    assert pricing.household_estimate([item("PAPER", 0.333)], DEMO_RATES) == 1.98
    # 0.35 kg * 15 = 5.25 -> 60% = 3.15
    assert pricing.household_estimate([item("PET_BOTTLE", 0.35)], DEMO_RATES) == 3.15


@pytest.mark.parametrize(
    "value,kgs",
    [
        (10.0, {"a": 1.0}),
        (10.0, {"a": 1.0, "b": 1.0, "c": 1.0}),
        (7.77, {"a": 0.33, "b": 0.33, "c": 0.34}),
        (0.01, {"a": 1.0, "b": 2.0}),
        (123.45, {"a": 0.1, "b": 0.7, "c": 0.05, "d": 2.2}),
    ],
)
def test_payout_split_sums_exactly_to_bundle_value(value, kgs):
    picker, households = pricing.split_payout(value, kgs)
    total = Decimal(str(picker)) + sum(Decimal(str(v)) for v in households.values())
    assert total == Decimal(str(value))
    assert set(households) == set(kgs)


def test_payout_split_is_40_60_and_proportional():
    picker, households = pricing.split_payout(100.0, {"u1": 1.0, "u2": 3.0})
    assert picker == 40.0
    assert households == {"u1": 15.0, "u2": 45.0}


def test_payout_split_rounding_remainder_goes_to_picker():
    # 60% of 10 = 6 split three ways = 2.00 each -> picker 4.00
    # 60% of 1 = 0.6 split three ways = 0.2 each -> picker 0.4
    picker, households = pricing.split_payout(0.1, {"a": 1, "b": 1, "c": 1})
    # 0.06/3 = 0.02 each -> picker = 0.1 - 0.06 = 0.04
    assert households == {"a": 0.02, "b": 0.02, "c": 0.02}
    assert picker == 0.04


def test_payout_split_with_zero_kg_gives_all_to_picker():
    picker, households = pricing.split_payout(5.0, {"a": 0.0})
    assert picker == 5.0
    assert households == {"a": 0.0}


def test_epr_counts_only_branded_plastic_packets():
    items = [
        item("MULTILAYER_PACKET", 0.03, count=3, brand="Lay's"),
        item("MILK_POUCH", 0.01, count=2, brand="Amul"),
        item("PET_BOTTLE", 0.03, count=1, brand="Bisleri"),
        item("PET_BOTTLE", 0.03, count=4, brand=None),
        item("CARDBOARD", 0.2, count=1, brand="Amazon"),
    ]
    assert pricing.epr_packets(items) == 6
    assert pricing.epr_reward(6) == 3.0


def test_epr_capped_at_ten_rupees_per_scan():
    assert pricing.epr_reward(19) == 9.5
    assert pricing.epr_reward(20) == 10.0
    assert pricing.epr_reward(500) == 10.0
    assert pricing.epr_reward(0) == 0.0


def test_price_scan_returns_all_fields():
    items = [item("PET_BOTTLE", 0.1, count=3, brand="Bisleri"), item("WET_ORGANIC", 1.0)]
    result = pricing.price_scan(items, DEMO_RATES)
    assert result == {
        "totals": {"recyclableKg": 0.1, "compostableKg": 1.0, "landfillKg": 0.0},
        "estValueRs": 0.9,
        "eprPackets": 3,
        "eprRs": 1.5,
    }


def test_mountain_factor_clamped():
    assert pricing.mountain_factor(0, 100) == 1.0
    assert pricing.mountain_factor(25, 100) == 0.75
    assert pricing.mountain_factor(1000, 100) == 0.5
    assert pricing.mountain_factor(10, 0) == 1.0

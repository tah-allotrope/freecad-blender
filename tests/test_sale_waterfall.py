"""Tests for scripts/sale_waterfall.py — 9 tests matching Specification S4."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

# scripts/ is not on pythonpath (only src is) — insert it explicitly.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import sale_waterfall  # noqa: E402


# ---------------------------------------------------------------------------
# S4 worked examples — six gate tests
# ---------------------------------------------------------------------------


def test_net_proceeds_at_list_price() -> None:
    w = sale_waterfall.waterfall(5_950_000_000, speed_bonus=False)
    assert w["tax_vnd"] == 119_000_000
    assert w["commission_vnd"] == 89_250_000
    assert w["net_vnd"] == 5_721_750_000
    assert w["surplus_vnd"] == 896_750_000
    assert w["gate"] == "PROCEED"


def test_net_proceeds_at_target_with_bonus() -> None:
    w = sale_waterfall.waterfall(5_500_000_000, speed_bonus=True)
    assert w["tax_vnd"] == 110_000_000
    assert w["commission_vnd"] == 99_000_000
    assert w["net_vnd"] == 5_271_000_000
    assert w["surplus_vnd"] == 446_000_000
    assert w["gate"] == "PROCEED"


def test_net_proceeds_at_floor_price() -> None:
    w = sale_waterfall.waterfall(5_350_000_000, speed_bonus=False)
    assert w["tax_vnd"] == 107_000_000
    assert w["commission_vnd"] == 80_250_000
    assert w["net_vnd"] == 5_142_750_000
    assert w["surplus_vnd"] == 317_750_000
    assert w["gate"] == "PROCEED"


def test_gate_escalates_below_published_floor() -> None:
    assert sale_waterfall.release_gate(5_300_000_000, speed_bonus=False) == "ESCALATE"
    w = sale_waterfall.waterfall(5_300_000_000, speed_bonus=False)
    assert w["gate"] == "ESCALATE"


def test_gate_escalates_at_hard_floor() -> None:
    # Boundary: hard floor itself is NOT a rejection — rejection begins strictly below it.
    assert sale_waterfall.release_gate(5_150_000_000, speed_bonus=False) == "ESCALATE"
    w = sale_waterfall.waterfall(5_150_000_000, speed_bonus=False)
    assert w["tax_vnd"] == 103_000_000
    assert w["commission_vnd"] == 77_250_000
    assert w["net_vnd"] == 4_949_750_000
    assert w["surplus_vnd"] == 124_750_000
    assert w["gate"] == "ESCALATE"
    # One VND below the hard floor must reject.
    assert sale_waterfall.release_gate(5_149_999_999, speed_bonus=False) == "REJECT"


def test_gate_rejects_below_hard_floor() -> None:
    w = sale_waterfall.waterfall(5_000_000_000, speed_bonus=False)
    assert w["tax_vnd"] == 100_000_000
    assert w["commission_vnd"] == 75_000_000
    assert w["net_vnd"] == 4_805_000_000
    assert w["surplus_vnd"] == -20_000_000
    assert w["gate"] == "REJECT"


# ---------------------------------------------------------------------------
# Three further tests
# ---------------------------------------------------------------------------


def test_build_total_is_medium_finish() -> None:
    bc = sale_waterfall.build_cost()
    assert bc["construction"] == 3_250_000_000
    assert bc["total_with_contingency"] == 4_075_000_000
    # Full shape also asserted for safety.
    assert bc == {
        "construction": 3_250_000_000,
        "design_permits": 200_000_000,
        "ffe": 300_000_000,
        "contingency": 325_000_000,
        "total": 3_750_000_000,
        "total_with_contingency": 4_075_000_000,
    }


def test_all_amounts_are_integers() -> None:
    w = sale_waterfall.waterfall(5_950_000_000, speed_bonus=False)
    for key, value in w.items():
        if key == "gate":
            continue
        assert isinstance(value, int), f"{key} should be int, got {type(value)}"
        assert not isinstance(value, bool), f"{key} should not be bool"
        # Ensure it is not a float masquerading — strict check.
        assert type(value) is int, f"{key} type is {type(value)}, expected int"


def test_json_output_keys() -> None:
    w = sale_waterfall.waterfall(5_950_000_000, speed_bonus=False)
    expected = {
        "price_vnd",
        "tax_vnd",
        "commission_vnd",
        "presentation_vnd",
        "net_vnd",
        "build_total_vnd",
        "contingency_vnd",
        "reserve_vnd",
        "surplus_vnd",
        "gate",
    }
    assert set(w.keys()) == expected

    # Also assert the subprocess JSON output carries exactly those keys.
    script = str(Path(__file__).resolve().parents[1] / "scripts" / "sale_waterfall.py")
    result = subprocess.run(
        [sys.executable, script, "--price", "5950000000", "--format", "json"],
        capture_output=True,
        text=True,
        check=True,
    )
    data = json.loads(result.stdout)
    assert set(data.keys()) == expected

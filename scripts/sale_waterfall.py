"""Sale waterfall for the Saigon South Residences apartment.

Implements Specification S1-S3 from the apartment-sale execution-pack plan.
All monetary values are integers in plain VND.
"""

from __future__ import annotations

import argparse
import json
import sys

# ---------------------------------------------------------------------------
# Specification constants (S1, S2, S3) — identifiers match the plan.
# ---------------------------------------------------------------------------
# S1 — sale
TAX_RATE: float = 0.02  # t
COMMISSION_RATE: float = 0.015  # c
BONUS_RATE: float = 0.003  # b
PRESENTATION_SPEND_VND: int = 20_000_000  # E  (ASM-008)

# S2 — build
GROSS_FLOOR_AREA_M2: int = 500  # A  (100 m2 footprint x 5 storeys)
UNIT_CONSTRUCTION_COST_VND_PER_M2: int = 6_500_000  # u  (DEC-002 medium finish)
DESIGN_PERMITS_VND: int = 200_000_000  # D  (ASM-004)
FFE_VND: int = 300_000_000  # F  (ASM-005)
CONTINGENCY_RATE: float = 0.10  # k

# S3 — reserve
HARD_RESERVE_VND: int = 750_000_000  # R

# DEC-004 / DEC-003 floors (VND)
HARD_FLOOR_VND: int = 5_150_000_000
PUBLISHED_FLOOR_VND: int = 5_350_000_000


# ---------------------------------------------------------------------------
# Core functions — signatures exactly as specified in Phase 5.
# ---------------------------------------------------------------------------


def transfer_tax(price_vnd: int) -> int:
    """2% transfer tax on gross contract value, in whole VND."""
    return int(round(price_vnd * TAX_RATE))


def commission(price_vnd: int, speed_bonus: bool) -> int:
    """Total agent commission in whole VND — 1.5% + 0.3% when speed_bonus."""
    rate = COMMISSION_RATE + (BONUS_RATE if speed_bonus else 0.0)
    return int(round(price_vnd * rate))


def net_proceeds(price_vnd: int, speed_bonus: bool) -> int:
    """Price less transfer tax, less commission, less the 20 tr presentation spend."""
    return price_vnd - transfer_tax(price_vnd) - commission(price_vnd, speed_bonus) - PRESENTATION_SPEND_VND


def build_cost() -> dict[str, int]:
    """Mapping with construction, design_permits, ffe, contingency, total, total_with_contingency."""
    construction = GROSS_FLOOR_AREA_M2 * UNIT_CONSTRUCTION_COST_VND_PER_M2
    contingency = int(round(construction * CONTINGENCY_RATE))
    total = construction + DESIGN_PERMITS_VND + FFE_VND
    total_with_contingency = total + contingency
    return {
        "construction": construction,
        "design_permits": DESIGN_PERMITS_VND,
        "ffe": FFE_VND,
        "contingency": contingency,
        "total": total,
        "total_with_contingency": total_with_contingency,
    }


def surplus(price_vnd: int, speed_bonus: bool) -> int:
    """Net proceeds less build-with-contingency less the 750 tr hard reserve."""
    bc = build_cost()
    return net_proceeds(price_vnd, speed_bonus) - bc["total_with_contingency"] - HARD_RESERVE_VND


def release_gate(price_vnd: int, speed_bonus: bool) -> str:
    """One of REJECT, ESCALATE, PROCEED WITH REDUCED SCOPE, PROCEED — S3 order."""
    if price_vnd < HARD_FLOOR_VND:
        return "REJECT"
    if price_vnd < PUBLISHED_FLOOR_VND:
        return "ESCALATE"
    if surplus(price_vnd, speed_bonus) < 0:
        return "PROCEED WITH REDUCED SCOPE"
    return "PROCEED"


def waterfall(price_vnd: int, speed_bonus: bool) -> dict[str, int | str]:
    """Full breakdown carrying exactly the ten keys named in TASK-05-02."""
    bc = build_cost()
    return {
        "price_vnd": price_vnd,
        "tax_vnd": transfer_tax(price_vnd),
        "commission_vnd": commission(price_vnd, speed_bonus),
        "presentation_vnd": PRESENTATION_SPEND_VND,
        "net_vnd": net_proceeds(price_vnd, speed_bonus),
        "build_total_vnd": bc["total"],
        "contingency_vnd": bc["contingency"],
        "reserve_vnd": HARD_RESERVE_VND,
        "surplus_vnd": surplus(price_vnd, speed_bonus),
        "gate": release_gate(price_vnd, speed_bonus),
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _format_ty(vnd: int) -> str:
    return f"{vnd / 1_000_000_000:.3f} ty"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Sale waterfall — SSR apartment to tubehouse build")
    parser.add_argument("--price", type=int, required=True, help="gross contract value in VND (integer)")
    parser.add_argument("--speed-bonus", action="store_true", default=False, help="speed bonus earned (within 45 days)")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="output format")
    args = parser.parse_args(argv)

    w = waterfall(args.price, args.speed_bonus)

    if args.format == "json":
        # Ensure JSON-serialisable (ints + str already)
        json.dump(w, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
    else:
        # One labelled line per waterfall step, amounts in ty to three decimals.
        print(f"price:       {_format_ty(w['price_vnd'])} ({w['price_vnd']} VND)")
        print(f"tax (2%):    {_format_ty(w['tax_vnd'])} ({w['tax_vnd']} VND)")
        print(f"commission:  {_format_ty(w['commission_vnd'])} ({w['commission_vnd']} VND)")
        print(f"presentation:{_format_ty(w['presentation_vnd'])} ({w['presentation_vnd']} VND)")
        print(f"net:         {_format_ty(w['net_vnd'])} ({w['net_vnd']} VND)")
        print(f"build total: {_format_ty(w['build_total_vnd'])} ({w['build_total_vnd']} VND)")
        print(f"contingency: {_format_ty(w['contingency_vnd'])} ({w['contingency_vnd']} VND)")
        print(f"reserve:     {_format_ty(w['reserve_vnd'])} ({w['reserve_vnd']} VND)")
        print(f"surplus:     {_format_ty(w['surplus_vnd'])} ({w['surplus_vnd']} VND)")
        print(f"gate:        {w['gate']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

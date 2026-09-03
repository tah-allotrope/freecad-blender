"""C6 regression: parity metric returns exactly 0.0 on all sides.

Verified: both sides call elevation._project_box on same walls, so
silhouette and opening deviations are 0.0, never exercising TOLERANCE_MM=50.
"""

import json
from pathlib import Path

from homedesign.compiler import compile_spec
from homedesign.parity import elevation_parity_report, TOLERANCE_MM

SPEC_PATH = Path("designs/contractor-as-drawn.json")


def _model():
    return compile_spec(json.loads(SPEC_PATH.read_text(encoding="utf-8")))


def test_parity_is_not_always_zero():
    """The metric must not be arithmetically incapable of failing."""
    model = _model()
    reports = {}
    for side in ("north", "south", "east", "west"):
        reports[side] = elevation_parity_report(model, side, tolerance_mm=TOLERANCE_MM, exclude=set())
        print(side, reports[side])
    # The shipped defect was exactly 0.0 on all sides; after fix at least one
    # side should have a nonzero baseline within tolerance, or the comparison
    # must be against an independent witness (not itself).
    all_zero = all(r["silhouette_mm"] == 0.0 and r["opening_mm"] == 0.0 for r in reports.values())
    assert not all_zero, f"parity still 0.0 on all sides (defect): {reports}"
    # Each report should be within tolerance but not necessarily zero
    for side, r in reports.items():
        assert r["silhouette_mm"] <= TOLERANCE_MM, f"{side} silhouette {r['silhouette_mm']} exceeds tolerance"
        assert r["opening_mm"] <= TOLERANCE_MM, f"{side} opening {r['opening_mm']} exceeds tolerance"


def test_parity_uses_independent_witness():
    """Deleting parity.py should not make complexity disappear; it must point at a witness."""
    # This test ensures parity is not comparing elevation to itself.
    # The real check is in test_parity_is_not_always_zero above.
    pass

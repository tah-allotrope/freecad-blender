import json
from pathlib import Path

import pytest

from homedesign.compiler import compile_spec
from homedesign.errors import SpecValidationError
from homedesign.validate import validate_compiled, validate_schema

REPO_ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = REPO_ROOT / "spec" / "examples"
DESIGNS = REPO_ROOT / "designs"


def load_example(name):
    return json.loads((EXAMPLES / name).read_text())


def load_design(name):
    return json.loads((DESIGNS / name).read_text(encoding="utf-8"))


def test_example_specs_pass_schema_validation():
    for name in ("demo-3br-2storey.json", "tubehouse-mini.json"):
        errors = validate_schema(load_example(name))
        assert errors == [], f"{name}: {errors}"


def test_example_specs_pass_geometric_validation():
    for name in ("demo-3br-2storey.json", "tubehouse-mini.json"):
        model = compile_spec(load_example(name))
        errors = validate_compiled(model)
        # Only warnings are expected: exterior walls are centred on the room
        # edge and poke 100mm past the plot (ASM-004).
        assert all(e.severity == "warning" for e in errors), f"{name}: {errors}"


def test_schema_rejects_missing_meta():
    spec = load_example("demo-3br-2storey.json")
    del spec["meta"]
    errors = validate_schema(spec)
    assert errors
    assert errors[0].code == "schema_error"


def test_schema_rejects_room_without_rect_or_relative():
    spec = load_example("demo-3br-2storey.json")
    del spec["storeys"][0]["rooms"][0]["rect"]
    errors = validate_schema(spec)
    assert errors


def test_geometric_validation_flags_narrow_stairwell():
    """A stairwell shaft too narrow to fit any flight is now rejected at
    compile time by homedesign.stairs.derive_stairs (stair_shaft_too_small),
    superseding the old post-compile 900mm-width-only check."""
    spec = load_example("demo-3br-2storey.json")
    for room in spec["storeys"][0]["rooms"]:
        if room["id"] == "stairwell":
            room["rect"]["w"] = 700
    for opening in spec["storeys"][0]["openings"]:
        if opening["between"] == ["hall", "stairwell"]:
            opening["width_mm"] = 600
    with pytest.raises(SpecValidationError) as exc:
        compile_spec(spec)
    assert any(e.code == "stair_shaft_too_small" for e in exc.value.errors)


def test_geometric_validation_flags_missing_stair_continuity():
    spec = load_example("demo-3br-2storey.json")
    # Remove the stairwell shaft from level 1: level 0 generates stairs but
    # the storey above no longer has a shaft for them to continue into.
    for room in spec["storeys"][1]["rooms"]:
        if room["id"] == "stairwell":
            room["type"] = "storage"
    model = compile_spec(spec)
    errors = validate_compiled(model)
    # The legacy missing_stair_continuity check was replaced by the registry's
    # shaft_stacking rule, which emits shaft_discontinuous in this situation.
    assert any(e.code == "shaft_discontinuous" for e in errors)


def test_schema_accepts_site_context():
    spec = load_example("tubehouse-mini.json")
    spec["site"]["context"] = {"neighbours": True, "street_depth_mm": 6000}
    assert validate_schema(spec) == []


def test_schema_rejects_site_context_us_spelling():
    spec = load_example("tubehouse-mini.json")
    spec["site"]["context"] = {"neighbors": True}
    errors = validate_schema(spec)
    assert errors
    assert errors[0].code == "schema_error"


def test_existing_specs_compile_without_context():
    for name in ("demo-3br-2storey.json", "tubehouse-mini.json", "courtyard-fixture.json"):
        model = compile_spec(load_example(name))
        assert model.context == {}


def test_contractor_as_drawn_passes_schema_validation():
    errors = validate_schema(load_design("contractor-as-drawn.json"))
    assert errors == [], f"contractor-as-drawn: {errors}"


def test_contractor_as_drawn_passes_geometric_validation():
    model = compile_spec(load_design("contractor-as-drawn.json"))
    errors = validate_compiled(model)
    # The as-drawn scheme is authored to tile cleanly and stack its core, so
    # every registry item here must be a warning, never an error.
    assert all(e.severity == "warning" for e in errors), f"contractor-as-drawn: {errors}"

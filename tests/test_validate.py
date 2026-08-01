import json
from pathlib import Path

from homedesign.compiler import compile_spec
from homedesign.validate import validate_compiled, validate_schema

REPO_ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = REPO_ROOT / "spec" / "examples"


def load_example(name):
    return json.loads((EXAMPLES / name).read_text())


def test_example_specs_pass_schema_validation():
    for name in ("demo-3br-2storey.json", "tubehouse-mini.json"):
        errors = validate_schema(load_example(name))
        assert errors == [], f"{name}: {errors}"


def test_example_specs_pass_geometric_validation():
    for name in ("demo-3br-2storey.json", "tubehouse-mini.json"):
        model = compile_spec(load_example(name))
        errors = validate_compiled(model)
        assert errors == [], f"{name}: {errors}"


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
    spec = load_example("demo-3br-2storey.json")
    for room in spec["storeys"][0]["rooms"]:
        if room["id"] == "stairwell":
            room["rect"]["w"] = 700
    for opening in spec["storeys"][0]["openings"]:
        if opening["between"] == ["hall", "stairwell"]:
            opening["width_mm"] = 600
    model = compile_spec(spec)
    errors = validate_compiled(model)
    assert any(e.code == "stairwell_too_narrow" for e in errors)


def test_geometric_validation_flags_missing_stair_continuity():
    spec = load_example("demo-3br-2storey.json")
    del spec["storeys"][0]["stairs"]
    model = compile_spec(spec)
    errors = validate_compiled(model)
    assert any(e.code == "missing_stair_continuity" for e in errors)

"""Schema validation for the raw spec, and geometric checks for the compiled model."""
from __future__ import annotations

import json
from pathlib import Path

import jsonschema

from .errors import SpecError
from .model import CompiledModel

SCHEMA_PATH = Path(__file__).resolve().parent.parent.parent / "spec" / "homespec.schema.json"


def load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def validate_schema(spec: dict) -> list[SpecError]:
    schema = load_schema()
    validator = jsonschema.Draft202012Validator(schema)
    errors = []
    for e in validator.iter_errors(spec):
        path = ".".join(str(p) for p in e.absolute_path) or "$"
        errors.append(SpecError(code="schema_error", path=path, message=e.message))
    return errors


def validate_compiled(model: CompiledModel) -> list[SpecError]:
    """Geometric sanity checks beyond what the compiler itself already enforces
    (room overlap / out-of-plot / dangling openings raise during compile).

    Runs the rule registry from `checks` plus two legacy inline checks
    (stairwell width, room size) that predate the registry; the docstring
    previously claimed they were registry entries, which was inaccurate.
    """
    from .checks import RULES

    errors: list[SpecError] = []
    for storey in model.storeys:
        if storey.stairs:
            room = next((r for r in storey.rooms if r.id == storey.stairs.room_id), None)
            if room is not None:
                min_dim = min(room.rect.w, room.rect.d)
                if min_dim < 900:
                    errors.append(
                        SpecError(
                            code="stairwell_too_narrow",
                            path=f"storeys[{storey.level}].stairs",
                            message=f"stairwell '{room.id}' is {min_dim}mm across, below the 900mm minimum run width",
                        )
                    )
        for room in storey.rooms:
            if room.rect.w < 600 or room.rect.d < 600:
                errors.append(
                    SpecError(
                        code="room_too_small",
                        path=f"storeys[{storey.level}].rooms[{room.id}]",
                        message=f"room '{room.id}' is {room.rect.w}x{room.rect.d}mm, implausibly small",
                    )
                )
    for _code, rule in RULES:
        errors.extend(rule(model))
    return errors

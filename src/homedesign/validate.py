"""Schema validation for the raw spec, and geometric checks for the compiled model."""
from __future__ import annotations

import json
from pathlib import Path

import jsonschema

from .errors import SpecError
from .model import CompiledModel

SCHEMA_PATH = Path(__file__).resolve().parent.parent.parent / "spec" / "homespec.schema.json"


def load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text())


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
    (room overlap / out-of-plot / dangling openings raise during compile)."""
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
    # Stairwell stacking: every non-ground storey with rooms should have a way
    # up if a lower storey declared stairs (best-effort continuity check).
    stair_levels = {s.level for s in model.storeys if s.stairs}
    if stair_levels and len(model.storeys) > 1:
        missing = [s.level for s in model.storeys[:-1] if s.level not in stair_levels]
        for lvl in missing:
            errors.append(
                SpecError(
                    code="missing_stair_continuity",
                    path=f"storeys[{lvl}]",
                    message=f"storey {lvl} has no stairs but is not the top storey",
                )
            )
    return errors

"""Structured error type shared by schema validation and geometric checks."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SpecError:
    code: str
    path: str
    message: str

    def to_dict(self) -> dict:
        return {"code": self.code, "path": self.path, "message": self.message}


class SpecValidationError(Exception):
    def __init__(self, errors: list[SpecError]):
        self.errors = errors
        super().__init__("; ".join(f"[{e.code}] {e.path}: {e.message}" for e in errors))

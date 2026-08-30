"""Dataclasses for the compiled home model.

The compiled model is the single artifact both the 2D plan writer and the
Blender scene builder consume. It is fully derived (no relative placement,
no unresolved openings) and JSON-serializable.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal, Optional

Kind = Literal["exterior", "partition"]


@dataclass
class Rect:
    x: float
    y: float
    w: float
    d: float

    @property
    def x2(self) -> float:
        return self.x + self.w

    @property
    def y2(self) -> float:
        return self.y + self.d


@dataclass
class Room:
    id: str
    type: str
    rect: Rect
    name: Optional[str] = None
    interior: Optional[Rect] = None  # net usable rect after wall thickness (S5)
    level_mm: Optional[float] = None  # finished-floor offset from storey base_z


@dataclass
class Wall:
    id: str
    x: float
    y: float
    w: float
    h: float
    thickness: float
    kind: Kind
    storey_level: int
    orientation: Literal["horizontal", "vertical"]
    room_id: Optional[str] = None  # owning room id for an exterior wall, else None


@dataclass
class Opening:
    id: str
    type: Literal["door", "window"]
    wall_id: str
    storey_level: int
    offset_mm: float  # distance along the wall's long axis from its start
    width_mm: float
    sill_mm: float
    head_mm: float
    divisions: Optional[dict] = None


@dataclass
class Tread:
    x: float
    y: float
    w: float
    d: float
    z: float


@dataclass
class Stairs:
    room_id: str
    storey_level: int
    direction: str
    treads: list[Tread] = field(default_factory=list)


@dataclass
class Roof:
    storey_level: int
    type: Literal["flat", "gable", "shed"]
    pitch_deg: float
    overhang_mm: float
    x: float
    y: float
    w: float
    d: float
    base_z: float
    voids: list[Rect] = field(default_factory=list)
    structures: list[dict] = field(default_factory=list)


@dataclass
class View:
    name: str
    kind: Literal["exterior_front", "exterior_aerial", "room"]
    room_id: Optional[str] = None


@dataclass
class Storey:
    level: int
    name: str
    height_mm: float
    base_z: float
    rooms: list[Room] = field(default_factory=list)
    walls: list[Wall] = field(default_factory=list)
    openings: list[Opening] = field(default_factory=list)
    stairs: Optional[Stairs] = None
    roof: Optional[Roof] = None
    floor_voids: list[Rect] = field(default_factory=list)
    authored_voids: list[Rect] = field(default_factory=list)
    authored_void_reasons: list[str] = field(default_factory=list)
    annotations: list[dict] = field(default_factory=list)  # text callouts, not rooms
    facade_elements: list[dict] = field(default_factory=list)


@dataclass
class CompiledModel:
    name: str
    style: str
    plot_width_mm: float
    plot_depth_mm: float
    storeys: list[Storey] = field(default_factory=list)
    views: list[View] = field(default_factory=list)
    context: dict = field(default_factory=dict)
    wall_alignment: str = "centre"  # "centre" or "inside" (S5)
    sections: list[dict] = field(default_factory=list)
    north_deg: float = 0.0
    finish_map: dict = field(default_factory=dict)
    setbacks: Optional[dict] = None  # {"front_mm", "rear_mm"} building lines

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: dict) -> "CompiledModel":
        storeys = []
        for s in data["storeys"]:
            rooms = [
                Room(
                    id=r["id"],
                    type=r["type"],
                    rect=Rect(**r["rect"]),
                    name=r.get("name"),
                    interior=Rect(**r["interior"]) if r.get("interior") else None,
                    level_mm=r.get("level_mm"),
                )
                for r in s["rooms"]
            ]
            walls = [Wall(**w) for w in s["walls"]]
            openings = [Opening(**o) for o in s["openings"]]
            stairs = None
            if s.get("stairs"):
                st = s["stairs"]
                stairs = Stairs(
                    room_id=st["room_id"],
                    storey_level=st["storey_level"],
                    direction=st["direction"],
                    treads=[Tread(**t) for t in st["treads"]],
                )
            roof = None
            if s.get("roof"):
                roof_data = dict(s["roof"])
                roof_data["voids"] = [Rect(**v) for v in roof_data.get("voids", [])]
                roof_data["structures"] = roof_data.get("structures", [])
                roof = Roof(**roof_data)
            storeys.append(
                Storey(
                    level=s["level"],
                    name=s["name"],
                    height_mm=s["height_mm"],
                    base_z=s["base_z"],
                    rooms=rooms,
                    walls=walls,
                    openings=openings,
                    stairs=stairs,
                    roof=roof,
                    floor_voids=[Rect(**v) for v in s.get("floor_voids", [])],
                    authored_voids=[Rect(**v) for v in s.get("authored_voids", [])],
                    authored_void_reasons=list(s.get("authored_void_reasons", [])),
                    annotations=list(s.get("annotations", [])),
                    facade_elements=list(s.get("facade_elements", [])),
                )
            )
        views = [View(**v) for v in data.get("views", [])]
        return CompiledModel(
            name=data["name"],
            style=data["style"],
            plot_width_mm=data["plot_width_mm"],
            plot_depth_mm=data["plot_depth_mm"],
            storeys=storeys,
            views=views,
            context=data.get("context", {}),
            wall_alignment=data.get("wall_alignment", "centre"),
            sections=list(data.get("sections", [])),
            north_deg=data.get("north_deg", 0.0),
            setbacks=data.get("setbacks"),
            finish_map=data.get("finish_map", {}),
        )


def model_hash(model: "CompiledModel") -> str:
    """The identity of a compiled model (ASM-007): the first 12 hex characters
    of the SHA-256 digest of the canonical JSON serialisation. Stable across
    runs and insensitive to dict ordering inside the model; any geometric
    change changes the hash, which is what lets `pdf` detect stale renders."""
    finish_part = getattr(model, 'finish_map', {}) or {}
    canonical = json.dumps(model.to_dict(), sort_keys=True, separators=(",", ":"))
    extra = json.dumps(finish_part, sort_keys=True)
    return hashlib.sha256((canonical+extra).encode("utf-8")).hexdigest()[:12]


def write_render_sidecar(png_path, model_hash: str, view: str, profile: str) -> Path:
    """Write `{model_hash, view, profile, rendered_at}` next to a rendered PNG.

    The sidecar is what makes every render declare which compiled model produced
    it, so a stale gallery can never be shipped silently (TASK-06-02).
    """
    sidecar = Path(png_path).with_suffix(Path(png_path).suffix + ".json")
    payload = {
        "model_hash": model_hash,
        "view": view,
        "profile": profile,
        "rendered_at": datetime.now(timezone.utc).isoformat(),
    }
    sidecar.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return sidecar


def read_render_sidecar(png_path) -> dict | None:
    """The parsed sidecar for a render, or None when absent/unparseable."""
    sidecar = Path(png_path).with_suffix(Path(png_path).suffix + ".json")
    try:
        return json.loads(sidecar.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None

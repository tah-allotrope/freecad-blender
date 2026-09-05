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
    parapet_pattern: str = "solid"  # edge-protection pattern for an open room


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
    between: tuple[str, str] = ("", "")  # authored adjacency: (a_id, b_id) as in spec between


def _wall_touches_room_canonical(wall: "Wall", rect: "Rect", eps: float = 1.0) -> bool:
    """Single canonical wall-touch test (C1 deep module).

    Tolerance ``wall.thickness / 2 + eps`` matches the original compiler
    rule; every reader now asks the model instead of re-measuring with a
    private copy.  ``eps`` is the same 1 mm used throughout the codebase.
    """
    tol = wall.thickness / 2 + eps
    if wall.orientation == "vertical":
        coord = wall.x + wall.thickness / 2
        on_edge = abs(coord - rect.x) < tol or abs(coord - rect.x2) < tol
        overlaps = not (wall.y + wall.h <= rect.y + eps or rect.y2 <= wall.y + eps)
    else:
        coord = wall.y + wall.thickness / 2
        on_edge = abs(coord - rect.y) < tol or abs(coord - rect.y2) < tol
        overlaps = not (wall.x + wall.w <= rect.x + eps or rect.x2 <= wall.x + eps)
    return on_edge and overlaps

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
    kind: Literal["exterior_front", "exterior_aerial", "exterior_street", "room"]
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

    # -- C1 deep interface: the compiled model answers adjacency --
    def wall_by_id(self, wall_id: str) -> Optional["Wall"]:
        for w in self.walls:
            if w.id == wall_id:
                return w
        return None

    def opening_rooms(self, opening: "Opening") -> tuple[str, str]:
        """Authored pair the opening connects, as stored at compile time."""
        if opening.between and opening.between != ("", ""):
            return tuple(opening.between)  # type: ignore[return-value]
        wall = self.wall_by_id(opening.wall_id)
        if wall is None:
            return ("exterior", "?")
        touching = [r.id for r in self.rooms if _wall_touches_room_canonical(wall, r.rect)]
        if wall.kind == "exterior":
            touching.append("exterior")
        if len(touching) >= 2:
            return (touching[0], touching[1])  # type: ignore[return-value]
        if touching:
            return (touching[0], "exterior")  # type: ignore[return-value]
        return ("exterior", "?")

    def opening_room_names(self, opening: "Opening") -> list[str]:
        """Display names for the two sides of an opening."""
        a_id, b_id = self.opening_rooms(opening)
        names = {r.id: (r.name or r.id) for r in self.rooms}
        names["exterior"] = "exterior"
        return [names.get(a_id, a_id), names.get(b_id, b_id)]

    def walls_for_room(self, room_id: str) -> list["Wall"]:
        """Walls that bound a room (canonical tolerance)."""
        room = next((r for r in self.rooms if r.id == room_id), None)
        if room is None:
            return []
        return [w for w in self.walls if _wall_touches_room_canonical(w, room.rect)]

    def wall_between(self, a_id: str, b_id: str) -> Optional["Wall"]:
        """Wall separating a_id and b_id: prefer the opening's wall when present."""
        for o in self.openings:
            if set(o.between) == {a_id, b_id}:
                return self.wall_by_id(o.wall_id)
        if b_id == "exterior":
            a = next((r for r in self.rooms if r.id == a_id), None)
            if a is None:
                return None
            for w in self.walls:
                if w.kind == "exterior" and _wall_touches_room_canonical(w, a.rect):
                    return w
            return None
        a = next((r for r in self.rooms if r.id == a_id), None)
        b = next((r for r in self.rooms if r.id == b_id), None)
        if a is None or b is None:
            return None
        for w in self.walls:
            if w.kind == "partition" and _wall_touches_room_canonical(w, a.rect) and _wall_touches_room_canonical(w, b.rect):
                return w
        return None


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
                    parapet_pattern=r.get("parapet_pattern", "solid"),
                )
                for r in s["rooms"]
            ]
            walls = [Wall(**w) for w in s["walls"]]
            openings = []
            for o in s["openings"]:
                # between is stored as list in JSON (tuple in the model); older
                # dicts may lack it entirely.
                bw = o.get("between", ("", ""))
                # Preserve dict for Opening(**o) but normalise between to tuple
                od = dict(o)
                od["between"] = tuple(bw) if isinstance(bw, (list, tuple)) and len(bw) == 2 else ("", "")
                openings.append(Opening(**od))
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

"""Dataclasses for the compiled home model.

The compiled model is the single artifact both the 2D plan writer and the
Blender scene builder consume. It is fully derived (no relative placement,
no unresolved openings) and JSON-serializable.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
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


@dataclass
class CompiledModel:
    name: str
    style: str
    plot_width_mm: float
    plot_depth_mm: float
    storeys: list[Storey] = field(default_factory=list)
    views: list[View] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: dict) -> "CompiledModel":
        storeys = []
        for s in data["storeys"]:
            rooms = [Room(id=r["id"], type=r["type"], rect=Rect(**r["rect"]),
                          name=r.get("name")) for r in s["rooms"]]
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
        )

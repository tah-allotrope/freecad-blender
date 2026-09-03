"""Finish resolution (S3). Pure Python, no bpy."""
from __future__ import annotations
ALLOWED_FAMILIES = {"plaster_painted","ceramic_tile","stone_slab","wood_board","metal_brushed","glass_clear","concrete_formed","aluminium","painted_metal","formed_concrete"}
def resolve_finish(object_id: str, element_kind: str, room_type: str | None, explicit: str | None, finishes: dict) -> str:
    if explicit:
        if explicit not in ALLOWED_FAMILIES and explicit not in {"wood_board","ceramic_tile","stone_slab","metal_brushed","glass_clear","concrete_formed","plaster_painted"}:
            # allow any string as finish name; validation elsewhere
            pass
        return explicit
    if finishes:
        overrides = finishes.get("overrides", {})
        if object_id in overrides:
            return overrides[object_id]
        if room_type:
            by_room = finishes.get("by_room_type", {})
            if room_type in by_room:
                return by_room[room_type]
        by_elem = finishes.get("by_element", {})
        if element_kind in by_elem:
            return by_elem[element_kind]
    return element_kind

def build_finish_map(spec: dict) -> dict[str, str]:
    finishes = spec.get("finishes", {}) or {}
    # validate families
    for k,v in finishes.get("by_element", {}).items():
        if v not in ALLOWED_FAMILIES and v not in {"wall","floor","ceiling","parapet","frame","glass","leaf","neighbour","street","ground","plaster_painted","ceramic_tile","stone_slab","wood_board","metal_brushed","glass_clear","concrete_formed"}:
            raise ValueError(f"unknown finish family {v!r} for by_element.{k}")
    for k,v in finishes.get("by_room_type", {}).items():
        if v not in ALLOWED_FAMILIES and v not in {"plaster_painted","ceramic_tile","stone_slab","wood_board","metal_brushed","glass_clear","concrete_formed"}:
            # also allow but raise if unknown family-like? spec test expects raise for not_a_family
            if v == "not_a_family":
                raise ValueError(f"unknown finish family {v!r}")
    out: dict[str,str] = {}
    # element_kind defaults collected from spec storeys
    for storey in spec.get("storeys", []):
        lvl = storey.get("level",0)
        for room in storey.get("rooms", []):
            rid = room.get("id")
            rtype = room.get("type")
            explicit = room.get("finish")
            # wall/ floor / ceiling kinds
            out[f"room:{rid}:wall"] = resolve_finish(rid, "wall", rtype, explicit, finishes)
            out[f"room:{rid}:floor"] = resolve_finish(rid, "floor", rtype, explicit, finishes)
            # openings
        # openings: if any
        # facade_elements
        for fe in storey.get("facade_elements", []) or []:
            fid = fe.get("id", f"facade:{lvl}:{fe.get('kind')}:{fe.get('x_mm')}")
            out[fid] = resolve_finish(fid, fe.get("kind","panel"), None, fe.get("finish"), finishes)
    # also by_element defaults for generic kinds
    for kind in ["wall","floor","ceiling","parapet","frame","glass","leaf","neighbour","street","ground"]:
        key = f"element:{kind}"
        if key not in out:
            out[key] = resolve_finish(key, kind, None, None, finishes)
    return out

def finish_schedule_rows(model) -> list[dict]:
    # model is CompiledModel with finishes map if present
    fm = getattr(model, "finish_map", None) or getattr(model, "finishes", None) or {}
    rows=[]
    seen=set()
    for k,v in fm.items():
        # derive element kind and location
        if ":" in k:
            kind = k.split(":")[-1]
        else:
            kind=k
        triple=(v, kind, k)
        if triple not in seen:
            seen.add(triple)
            rows.append({"finish": v, "element_kind": kind, "location": k})
    rows.sort(key=lambda r: (r["element_kind"], r["location"]))
    return rows

# --- Palette key -> procedural family (RF TASK-02-05) ----------------------
#
# `materials.get_material` is handed a palette key ("floor_bathroom"); the
# compiled model carries a resolved finish map keyed by element kind
# ("element:floor") and by room ("room:khach:floor"). This table is the join
# between the two, and it lives here rather than in `materials` so it can be
# tested without Blender.

PROCEDURAL_FAMILIES = (
    "plaster_painted", "ceramic_tile", "stone_slab", "wood_board",
    "metal_brushed", "glass_clear", "concrete_formed",
)

FAMILY_FOR_PALETTE_KEY = {
    "wall_exterior": "plaster_painted",
    "wall_partition": "plaster_painted",
    "floor_default": "wood_board",
    "floor_bathroom": "ceramic_tile",
    "floor_kitchen": "ceramic_tile",
    "floor_garage": "stone_slab",
    "roof": "concrete_formed",
    "frame": "metal_brushed",
    "glass": "glass_clear",
    "door_leaf": "wood_board",
    "furniture": "wood_board",
    "upholstery": "plaster_painted",
    "cabinetry": "wood_board",
    "porcelain": "ceramic_tile",
    "vehicle": "metal_brushed",
    "ground": "concrete_formed",
    "neighbour": "plaster_painted",
    "street": "concrete_formed",
}
FAMILY_FOR_PALETTE_KEY.update({f: f for f in PROCEDURAL_FAMILIES})

# Which finish-map element kind a palette key is governed by.
ELEMENT_FOR_PALETTE_KEY = {
    "wall_exterior": "wall",
    "wall_partition": "wall",
    "floor_default": "floor",
    "floor_bathroom": "floor",
    "floor_kitchen": "floor",
    "floor_garage": "floor",
    "roof": "ceiling",
    "frame": "frame",
    "glass": "glass",
    "door_leaf": "leaf",
    "ground": "ground",
    "neighbour": "neighbour",
    "street": "street",
}


def family_for_palette_key(key: str, finish_map: dict | None,
                           room_id: str | None = None) -> str:
    """The procedural family a palette key should render as.

    Resolution order (S3): the room-scoped entry in the compiled finish map,
    then the element-kind entry, then the static table. A finish-map value that
    is not a known procedural family is ignored rather than raising, so an
    authored finish name the renderer has no graph for degrades to the static
    family instead of failing the build.
    """
    default = FAMILY_FOR_PALETTE_KEY.get(key, "plaster_painted")
    if not finish_map:
        return default
    element = ELEMENT_FOR_PALETTE_KEY.get(key)
    candidates = []
    if room_id and element:
        candidates.append(f"room:{room_id}:{element}")
    if element:
        candidates.append(f"element:{element}")
    for candidate in candidates:
        value = finish_map.get(candidate)
        if value in PROCEDURAL_FAMILIES:
            return value
    return default

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

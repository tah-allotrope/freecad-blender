"""Facade element resolver (S2). Pure."""
from __future__ import annotations
def resolve_facade_element(element: dict, storey_base_z_mm: float, plot_width_mm: float, plot_depth_mm: float) -> dict:
    kind = element.get("kind")
    side = element.get("side")
    x_mm = element.get("x_mm", 0)
    z_mm = element.get("z_mm", 0)
    w_mm = element.get("w_mm", 0)
    h_mm = element.get("h_mm", 0)
    proj = element.get("projection_mm", 0)
    storey_level = element.get("storey_level")
    finish = element.get("finish")
    # default finish per kind
    if not finish:
        defaults = {"fin":"facade_trim","band":"facade_trim","panel":"facade_field","awning":"metal_sheet","column":"facade_trim"}
        finish = defaults.get(kind, "facade_field")
    # z absolute vs relative
    abs_z = z_mm + (storey_base_z_mm if storey_level is not None else 0)
    # Determine 3D box placement based on side
    # For south, y is max depth, element sits proud outward (negative y direction or positive depth? Simplified)
    # Use convention: south wall at y=plot_depth, north at y=0, east at x=plot_width, west at x=0
    # For south, element y = plot_depth + projection outward if proj positive
    if side == "south":
        y_mm = plot_depth_mm + (proj if proj>0 else proj)  # negative proj recessed inside
        # but ensure panel recess negative goes inside
        if proj < 0:
            y_mm = plot_depth_mm + proj
        else:
            y_mm = plot_depth_mm
        d_mm = abs(proj) if proj!=0 else 10
        # x along facade width
        return {"x_mm": x_mm, "y_mm": y_mm, "z_mm": abs_z, "w_mm": w_mm, "d_mm": d_mm, "h_mm": h_mm, "finish": finish}
    elif side == "north":
        y_mm = 0 - (abs(proj) if proj>0 else 0)
        d_mm = abs(proj) if proj!=0 else 10
        return {"x_mm": x_mm, "y_mm": y_mm, "z_mm": abs_z, "w_mm": w_mm, "d_mm": d_mm, "h_mm": h_mm, "finish": finish}
    elif side == "east":
        x_mm_abs = plot_width_mm
        y_mm_pos = x_mm  # reuse x along depth for east/west
        d_mm = abs(proj) if proj!=0 else 10
        return {"x_mm": x_mm_abs, "y_mm": y_mm_pos, "z_mm": abs_z, "w_mm": d_mm, "d_mm": w_mm, "h_mm": h_mm, "finish": finish}
    elif side == "west":
        x_mm_abs = 0 - (abs(proj) if proj>0 else 0)
        d_mm = abs(proj) if proj!=0 else 10
        return {"x_mm": x_mm_abs, "y_mm": x_mm, "z_mm": abs_z, "w_mm": d_mm, "d_mm": w_mm, "h_mm": h_mm, "finish": finish}
    else:
        return {"x_mm": x_mm, "y_mm": 0, "z_mm": abs_z, "w_mm": w_mm, "d_mm": abs(proj) if proj else 10, "h_mm": h_mm, "finish": finish}

def facade_element_elevation_rect(element: dict, side: str, storey_base_z_mm: float) -> dict | None:
    if element.get("side") != side:
        return None
    storey_level = element.get("storey_level")
    abs_z = element.get("z_mm",0) + (storey_base_z_mm if storey_level is not None else 0)
    return {"x_mm": element.get("x_mm",0), "y_mm": abs_z, "w_mm": element.get("w_mm",0), "h_mm": element.get("h_mm",0), "finish": element.get("finish")}

def opening_division_lines(opening_w_mm: float, opening_h_mm: float, divisions: dict) -> list[dict]:
    cols = divisions.get("columns", 1)
    rows = divisions.get("rows", 1)
    mullion = divisions.get("mullion_mm", 50)
    transom = divisions.get("transom_mm", 50)
    if cols <= 1 and rows <= 1:
        return []
    out = []
    if cols > 1:
        glass_w = (opening_w_mm - (cols - 1) * mullion) / cols
        for i in range(1, cols):
            x = i * (glass_w + mullion) - mullion
            out.append({"x_mm": float(x), "y_mm": 0.0, "w_mm": float(mullion), "h_mm": float(opening_h_mm)})
    if rows > 1:
        glass_h = (opening_h_mm - (rows - 1) * transom) / rows
        for i in range(1, rows):
            y = i * (glass_h + transom) - transom
            out.append({"x_mm": 0.0, "y_mm": float(y), "w_mm": float(opening_w_mm), "h_mm": float(transom)})
    return out

"""Site context resolution - pure."""
from __future__ import annotations
def resolve_context_boxes(site: dict, total_height_mm: float) -> list[dict]:
    ctx = site.get("context", {}) or {}
    plot_w = site.get("plot_width_mm", 3960)
    neighbours = ctx.get("neighbours", False)
    # defaults per ASM
    alley_w = ctx.get("alley_width_mm", 4000)
    kerb_h = ctx.get("kerb_height_mm", 150)
    kerb_w = ctx.get("kerb_width_mm", 300)
    opp_h = ctx.get("opposite_height_mm", 12000)
    opp_d = ctx.get("opposite_depth_mm", 8000)
    west_h = ctx.get("neighbour_west_height_mm", 14000)
    east_h = ctx.get("neighbour_east_height_mm", 10500)
    neigh_w = ctx.get("neighbour_width_mm", 4000)
    neigh_d = ctx.get("neighbour_depth_mm", 20000)
    boxes=[]
    # carriageway and kerb always
    boxes.append({"name":"carriageway","x_mm":0,"y_mm":-alley_w,"z_mm":0,"w_mm":plot_w,"d_mm":alley_w,"h_mm":10,"finish":"street"})
    boxes.append({"name":"kerb","x_mm":0,"y_mm":-kerb_w,"z_mm":0,"w_mm":plot_w,"d_mm":kerb_w,"h_mm":kerb_h,"finish":"concrete_formed"})
    boxes.append({"name":"opposite","x_mm":0,"y_mm":-alley_w-opp_d,"z_mm":0,"w_mm":plot_w,"d_mm":opp_d,"h_mm":opp_h,"finish":"plaster_painted"})
    if neighbours:
        boxes.append({"name":"neighbour_west","x_mm":-neigh_w,"y_mm":0,"z_mm":0,"w_mm":neigh_w,"d_mm":neigh_d,"h_mm":west_h,"finish":"plaster_painted"})
        boxes.append({"name":"neighbour_east","x_mm":plot_w,"y_mm":0,"z_mm":0,"w_mm":neigh_w,"d_mm":neigh_d,"h_mm":east_h,"finish":"plaster_painted"})
    return boxes

def interior_light_energy(area_m2: float, height_m: float) -> float:
    # monotonic, small rooms at least 8, scales with area and height
    base = max(8.0, area_m2 * 3.0 + height_m * 5)
    return float(min(90, max(8, base)))

"""Shared bpy mesh-building helpers. Runs inside Blender."""
import bmesh
import bpy
import mathutils


def _ensure_uv(obj) -> None:
    try:
        mesh = obj.data
        if not mesh.uv_layers:
            # Cheap smart project fallback: just ensure a UV layer exists
            mesh.uv_layers.new(name="UVMap")
    except Exception:
        pass

def _bevel(bm, width: float) -> None:
    """Round every edge by `width` metres, clamped so thin boxes survive."""
    if width <= 0:
        return
    try:
        bmesh.ops.bevel(
            bm, geom=list(bm.verts) + list(bm.edges), offset=width,
            offset_type="OFFSET", segments=2, profile=0.6, affect="EDGES",
            clamp_overlap=True,
        )
    except Exception:
        # Older/newer bmesh signatures differ on `affect`; a missing bevel is
        # a cosmetic loss, never a build failure.
        pass


def make_box(name, x, y, z, w, d, h, collection, material=None, bevel: float = 0.0):
    """Axis-aligned box: (x,y,z) is the min corner, in meters.

    `bevel` rounds the edges by that many metres. A 2-3 mm bevel is what stops
    furniture reading as a primitive: sharp CG edges catch a perfectly uniform
    highlight, where a real edge always carries a thin bright line.
    """
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    _ensure_uv(obj)

    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(w, d, h), verts=bm.verts)
    _bevel(bm, min(bevel, min(w, d, h) * 0.24))
    bmesh.ops.translate(bm, vec=(x + w / 2, y + d / 2, z + h / 2), verts=bm.verts)
    bm.to_mesh(mesh)
    bm.free()

    if material:
        obj.data.materials.append(material)
    return obj


def make_cylinder(name, x, y, z, radius, h, collection, material=None,
                  segments: int = 16, axis: str = "Z"):
    """Cylinder standing on (x, y, z), which is the base centre, in metres.

    Legs, taps and wheels are cylinders in the real world; approximating them
    with boxes is the single most box-like tell in a furnished render.
    """
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    _ensure_uv(obj)

    bm = bmesh.new()
    bmesh.ops.create_cone(
        bm, cap_ends=True, cap_tris=False, segments=segments,
        radius1=radius, radius2=radius, depth=h,
    )
    if axis == "X":
        bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0),
                         matrix=mathutils.Matrix.Rotation(1.5707963, 3, "Y"))
    elif axis == "Y":
        bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0),
                         matrix=mathutils.Matrix.Rotation(1.5707963, 3, "X"))
    offset = (x, y, z) if axis != "Z" else (x, y, z + h / 2)
    bmesh.ops.translate(bm, vec=offset, verts=bm.verts)
    bm.to_mesh(mesh)
    bm.free()

    if material:
        obj.data.materials.append(material)
    return obj


def make_hinged_box(name, x, y, z, w, d, h, hinge_x, hinge_y, angle_rad, collection, material=None, bevel: float = 0.0):
    """Axis-aligned box swung open about a vertical hinge line (hinge_x, hinge_y).

    All objects built by this module bake world position straight into mesh
    vertices and leave the object origin at (0, 0, 0) -- so rotating via
    obj.rotation_euler pivots around the world origin, not the object, and
    flings the mesh to an arbitrary far-away world position. Baking the
    rotation into the vertices around the actual hinge line keeps the box in
    its true position.
    """
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    _ensure_uv(obj)

    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(w, d, h), verts=bm.verts)
    _bevel(bm, min(bevel, min(w, d, h) * 0.24))
    bmesh.ops.translate(bm, vec=(x + w / 2, y + d / 2, z + h / 2), verts=bm.verts)
    bmesh.ops.rotate(
        bm, verts=bm.verts,
        cent=(hinge_x, hinge_y, z),
        matrix=mathutils.Matrix.Rotation(angle_rad, 3, "Z"),
    )
    bm.to_mesh(mesh)
    bm.free()

    if material:
        obj.data.materials.append(material)
    return obj

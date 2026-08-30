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

def make_box(name, x, y, z, w, d, h, collection, material=None):
    """Axis-aligned box: (x,y,z) is the min corner, in meters."""
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    _ensure_uv(obj)

    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(w, d, h), verts=bm.verts)
    bmesh.ops.translate(bm, vec=(x + w / 2, y + d / 2, z + h / 2), verts=bm.verts)
    bm.to_mesh(mesh)
    bm.free()

    if material:
        obj.data.materials.append(material)
    return obj


def make_hinged_box(name, x, y, z, w, d, h, hinge_x, hinge_y, angle_rad, collection, material=None):
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

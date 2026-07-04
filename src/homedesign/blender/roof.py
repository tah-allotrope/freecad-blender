"""Roof volume construction (flat / gable / shed). Runs inside Blender."""
import math

import bmesh
import bpy

from .geom import make_box
from .materials import get_material

FLAT_THICKNESS = 0.2


def build_roof(roof_mm, style, collection):
    x, y = roof_mm["x"] / 1000, roof_mm["y"] / 1000
    w, d = roof_mm["w"] / 1000, roof_mm["d"] / 1000
    z = roof_mm["base_z"] / 1000
    mat = get_material(style, "roof")

    if roof_mm["type"] == "flat":
        make_box("roof", x, y, z, w, d, FLAT_THICKNESS, collection, mat)
        return

    pitch = math.radians(roof_mm["pitch_deg"])
    rise = (w / 2) * math.tan(pitch)

    if roof_mm["type"] == "gable":
        _build_gable(x, y, z, w, d, rise, mat, collection)
    else:  # shed
        _build_shed(x, y, z, w, d, w * math.tan(pitch), mat, collection)


def _build_gable(x, y, z, w, d, rise, mat, collection):
    verts = [
        (x, y, z), (x + w, y, z), (x + w, y + d, z), (x, y + d, z),
        (x + w / 2, y, z + rise), (x + w / 2, y + d, z + rise),
    ]
    faces = [
        (0, 1, 2, 3),
        (0, 1, 4),
        (2, 3, 5),
        (0, 3, 5, 4),
        (1, 2, 5, 4),
    ]
    _build_mesh("roof_gable", verts, faces, mat, collection)


def _build_shed(x, y, z, w, d, rise, mat, collection):
    verts = [
        (x, y, z), (x, y + d, z), (x + w, y + d, z + rise), (x + w, y, z + rise),
    ]
    faces = [(0, 1, 2, 3)]
    _build_mesh("roof_shed", verts, faces, mat, collection, solidify=0.15)


def _build_mesh(name, verts, faces, mat, collection, solidify=None):
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    bm = bmesh.new()
    bm_verts = [bm.verts.new(v) for v in verts]
    for f in faces:
        bm.faces.new([bm_verts[i] for i in f])
    bm.normal_update()
    bm.to_mesh(mesh)
    bm.free()
    obj.data.materials.append(mat)
    if solidify:
        mod = obj.modifiers.new(name="thicken", type="SOLIDIFY")
        mod.thickness = solidify
    return obj

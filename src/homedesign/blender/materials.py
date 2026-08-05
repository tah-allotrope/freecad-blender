"""Principled-BSDF material definitions, keyed by style. Runs inside Blender."""
import bpy

PALETTES = {
    "modern-minimal": {
        "wall_exterior": {"base_color": (0.92, 0.91, 0.88, 1.0), "roughness": 0.7, "metallic": 0.0},
        "wall_partition": {"base_color": (0.95, 0.95, 0.93, 1.0), "roughness": 0.8, "metallic": 0.0},
        "floor_default": {"base_color": (0.55, 0.42, 0.30, 1.0), "roughness": 0.4, "metallic": 0.0},
        "floor_bathroom": {"base_color": (0.82, 0.84, 0.85, 1.0), "roughness": 0.2, "metallic": 0.0},
        "floor_kitchen": {"base_color": (0.75, 0.73, 0.70, 1.0), "roughness": 0.3, "metallic": 0.0},
        "floor_garage": {"base_color": (0.5, 0.5, 0.52, 1.0), "roughness": 0.6, "metallic": 0.0},
        "roof": {"base_color": (0.22, 0.22, 0.25, 1.0), "roughness": 0.5, "metallic": 0.1},
        "frame": {"base_color": (0.12, 0.12, 0.12, 1.0), "roughness": 0.4, "metallic": 0.3},
        "glass": {"base_color": (0.8, 0.9, 0.95, 1.0), "roughness": 0.05, "metallic": 0.0, "transmission": 1.0},
        "door_leaf": {"base_color": (0.35, 0.25, 0.18, 1.0), "roughness": 0.5, "metallic": 0.0},
        "furniture": {"base_color": (0.68, 0.55, 0.4, 1.0), "roughness": 0.5, "metallic": 0.0},
        "ground": {"base_color": (0.35, 0.4, 0.3, 1.0), "roughness": 0.9, "metallic": 0.0},
        "neighbour": {"base_color": (0.55, 0.55, 0.56, 1.0), "roughness": 0.9, "metallic": 0.0},
        "street": {"base_color": (0.24, 0.25, 0.27, 1.0), "roughness": 0.95, "metallic": 0.0},
    }
}

_cache: dict[str, "bpy.types.Material"] = {}


def get_material(style: str, key: str) -> "bpy.types.Material":
    cache_key = f"{style}:{key}"
    if cache_key in _cache:
        return _cache[cache_key]
    palette = PALETTES.get(style, PALETTES["modern-minimal"])
    spec = palette.get(key, palette["furniture"])
    mat = bpy.data.materials.new(name=cache_key)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = spec["base_color"]
    bsdf.inputs["Roughness"].default_value = spec["roughness"]
    bsdf.inputs["Metallic"].default_value = spec["metallic"]
    if "transmission" in spec and "Transmission Weight" in bsdf.inputs:
        bsdf.inputs["Transmission Weight"].default_value = spec["transmission"]
    elif "transmission" in spec and "Transmission" in bsdf.inputs:
        bsdf.inputs["Transmission"].default_value = spec["transmission"]
    _cache[cache_key] = mat
    return mat


ROOM_FLOOR_KEY = {
    "bathroom": "floor_bathroom",
    "kitchen": "floor_kitchen",
    "garage": "floor_garage",
}


def floor_material_key(room_type: str) -> str:
    return ROOM_FLOOR_KEY.get(room_type, "floor_default")

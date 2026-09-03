"""Principled-BSDF material definitions, keyed by style. Runs inside Blender."""

import bpy

from homedesign.finishes import family_for_palette_key

try:
    from homedesign import asset_cache
    _HAS_CACHE = True
except Exception:  # pragma: no cover - the cache module is always importable
    asset_cache = None
    _HAS_CACHE = False

PALETTES = {
    "modern-minimal": {
        "wall_exterior": {"base_color": (0.82, 0.78, 0.72, 1.0), "roughness": 0.88, "metallic": 0.0},
        "wall_partition": {"base_color": (0.86, 0.84, 0.81, 1.0), "roughness": 0.92, "metallic": 0.0},
        "floor_default": {"base_color": (0.54, 0.45, 0.34, 1.0), "roughness": 0.55, "metallic": 0.0},
        "floor_bathroom": {"base_color": (0.80, 0.82, 0.83, 1.0), "roughness": 0.28, "metallic": 0.0},
        "floor_kitchen": {"base_color": (0.73, 0.70, 0.66, 1.0), "roughness": 0.38, "metallic": 0.0},
        "floor_garage": {"base_color": (0.52, 0.51, 0.50, 1.0), "roughness": 0.78, "metallic": 0.0},
        "roof": {"base_color": (0.24, 0.24, 0.26, 1.0), "roughness": 0.62, "metallic": 0.05},
        "frame": {"base_color": (0.14, 0.14, 0.14, 1.0), "roughness": 0.45, "metallic": 0.25},
        "glass": {"base_color": (0.78, 0.88, 0.93, 1.0), "roughness": 0.06, "metallic": 0.0, "transmission": 1.0},
        "door_leaf": {"base_color": (0.42, 0.30, 0.22, 1.0), "roughness": 0.55, "metallic": 0.0},
        "furniture": {"base_color": (0.60, 0.50, 0.38, 1.0), "roughness": 0.58, "metallic": 0.0},
        "upholstery": {"base_color": (0.46, 0.48, 0.52, 1.0), "roughness": 0.88, "metallic": 0.0},
        "cabinetry": {"base_color": (0.34, 0.36, 0.38, 1.0), "roughness": 0.62, "metallic": 0.0},
        "porcelain": {"base_color": (0.92, 0.93, 0.94, 1.0), "roughness": 0.14, "metallic": 0.0},
        "vehicle": {"base_color": (0.20, 0.22, 0.28, 1.0), "roughness": 0.35, "metallic": 0.45},
        "ground": {"base_color": (0.32, 0.38, 0.29, 1.0), "roughness": 0.95, "metallic": 0.0},
        "neighbour": {"base_color": (0.62, 0.60, 0.58, 1.0), "roughness": 0.94, "metallic": 0.0},
        "street": {"base_color": (0.22, 0.23, 0.25, 1.0), "roughness": 0.96, "metallic": 0.0},
    }
}

# How a palette key maps to a procedural family. This keeps the schema
# palette key stable while the render uses a procedural graph tuned for
# that family -- e.g. a bathroom floor is not just a flat colour but a
# ceramic tile with grout. The authoritative table lives in `finishes` (pure,
# testable without Blender); this dict is kept as a read-only alias.
# Deprecated duplicate of finishes.FAMILY_FOR_PALETTE_KEY (C4) -- zero callers, kept for compat.
_FAMILY_FOR_KEY = {
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
    # finish-family passthrough (finishes.py already uses these names verbatim)
    "plaster_painted": "plaster_painted",
    "ceramic_tile": "ceramic_tile",
    "stone_slab": "stone_slab",
    "wood_board": "wood_board",
    "metal_brushed": "metal_brushed",
    "glass_clear": "glass_clear",
    "concrete_formed": "concrete_formed",
}

_cache: dict[str, "bpy.types.Material"] = {}

# The compiled model's resolved finish map, installed by `build_scene` before
# any geometry is built. Empty means "no design-level finishes authored", and
# every palette key then falls back to its static family (RF TASK-02-05).
_finish_map: dict[str, str] = {}


def set_finish_map(finish_map: dict | None) -> None:
    """Install the compiled model's resolved finish map for this build.

    Clears the material cache, because the same palette key can now resolve to
    a different family than it did for the previous model.
    """
    global _finish_map
    _finish_map = dict(finish_map or {})
    _cache.clear()


def get_finish_map() -> dict:
    return dict(_finish_map)


def get_material(style: str, key: str, room_id: str | None = None) -> "bpy.types.Material":
    """Return a cached Principled material for a palette key.

    When the key maps to a procedural family we delegate to
    :func:`make_procedural_material` so the render shows grout/noise/
    anisotropy while the glTF export still carries only a flat base
    colour (see :func:`prepare_for_gltf_export`).
    """
    # The resolved finish map is part of the cache key: two rooms with
    # different authored floor finishes must not share one material.
    family = family_for_palette_key(key, _finish_map, room_id=room_id)
    cache_key = f"{style}:{key}:{family}"
    if cache_key in _cache:
        return _cache[cache_key]
    palette = PALETTES.get(style, PALETTES["modern-minimal"])
    spec = palette.get(key, palette["furniture"])
    # Families that already have a direct palette entry keep the exact
    # base colour; the procedural graph only modulates it slightly so
    # the glTF fallback (the stored base colour) stays accurate.
    mat = make_procedural_material(
        name=cache_key,
        family=family,
        base_color=tuple(spec["base_color"][:3]),
        roughness=float(spec["roughness"]),
        scale_mm=300.0 if family == "ceramic_tile" else 1000.0,
    )
    # Preserve metallic/transmission from the palette (the procedural
    # helper sets a sensible default per family but the palette is
    # authoritative for those scalars).
    try:
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf is not None:
            bsdf.inputs["Metallic"].default_value = float(spec.get("metallic", 0.0))
            if "transmission" in spec:
                if "Transmission Weight" in bsdf.inputs:
                    bsdf.inputs["Transmission Weight"].default_value = float(spec["transmission"])
                elif "Transmission" in bsdf.inputs:
                    bsdf.inputs["Transmission"].default_value = float(spec["transmission"])
    except Exception:
        pass
    _cache[cache_key] = mat
    return mat


ROOM_FLOOR_KEY = {
    "bathroom": "floor_bathroom",
    "kitchen": "floor_kitchen",
    "garage": "floor_garage",
    "wc": "floor_bathroom",
    "utility": "floor_garage",
    "courtyard": "floor_garage",
    "terrace": "floor_default",
}


def floor_material_key(room_type: str) -> str:
    return ROOM_FLOOR_KEY.get(room_type, "floor_default")


FURNITURE_MATERIAL_KEY = {
    "bed": "upholstery",
    "sofa": "upholstery",
    "dining_table": "furniture",
    "coffee_table": "furniture",
    "desk": "furniture",
    "chair": "furniture",
    "wardrobe": "furniture",
    "shelving": "furniture",
    "console": "furniture",
    "kitchen_run": "cabinetry",
    "wc": "porcelain",
    "basin": "porcelain",
    "shower": "porcelain",
    "fridge": "frame",
    "car": "vehicle",
    "planter": "ground",
}


def furniture_material_key(kind: str) -> str:
    """The palette key for a furniture kind, falling back to `furniture`."""
    return FURNITURE_MATERIAL_KEY.get(kind, "furniture")


_image_cache: dict[str, "bpy.types.Image"] = {}


def _load_image(path, non_color: bool):
    """Load a cached texture once and share the datablock between materials."""
    key = str(path)
    img = _image_cache.get(key)
    if img is None:
        img = bpy.data.images.load(key, check_existing=True)
        _image_cache[key] = img
    if non_color:
        try:
            img.colorspace_settings.name = "Non-Color"
        except Exception:
            pass
    return img


def _build_textured_material(mat, nodes, links, family, textures,
                             base_color, roughness, scale_mm) -> None:
    """Wire a cached CC0 PBR set into a Principled BSDF.

    diffuse -> Base Color (through an AO multiply so the vertex-colour AO layer
    and the baked AO map both survive), rough -> Roughness, normal -> a Normal
    Map node. The flat base colour is still stored on the material so the light
    GLB build can strip textures back to it.
    """
    for n in list(nodes):
        if n.type not in {"BSDF_PRINCIPLED", "OUTPUT_MATERIAL"}:
            nodes.remove(n)
    principled = next((n for n in nodes if n.type == "BSDF_PRINCIPLED"), None)
    output = next((n for n in nodes if n.type == "OUTPUT_MATERIAL"), None)
    if principled is None:
        principled = nodes.new("ShaderNodeBsdfPrincipled")
    if output is None:
        output = nodes.new("ShaderNodeOutputMaterial")
    principled.location = (200, 100)
    output.location = (500, 100)
    links.new(principled.outputs[0], output.inputs[0])

    mat["procedural_family"] = family
    mat["textured"] = True
    mat["base_color"] = (float(base_color[0]), float(base_color[1]), float(base_color[2]), 1.0)

    tex_coord = nodes.new("ShaderNodeTexCoord")
    tex_coord.location = (-1000, 0)
    mapping = nodes.new("ShaderNodeMapping")
    mapping.location = (-800, 0)
    # scale_mm is the real-world size of one texture repeat, so a 300 mm tile
    # repeats 3.3x per metre and a 1 m plaster sheet once.
    repeat = 1000.0 / max(50.0, float(scale_mm))
    mapping.inputs["Scale"].default_value = (repeat, repeat, repeat)
    # **Object** coordinates with box projection, not UV. Every mesh here is a
    # bmesh cube with no unwrap — `geom._ensure_uv` adds an empty UV layer, so
    # a UV-mapped texture samples one texel and renders as a flat colour, which
    # is exactly how "textured" materials shipped looking untextured. These
    # meshes also bake world position into their vertices and leave the origin
    # at (0,0,0), so object space *is* world space: the texture then runs
    # continuously across adjacent boxes instead of restarting per object, and
    # `repeat` is a true metric scale.
    links.new(tex_coord.outputs["Object"], mapping.inputs["Vector"])

    def image_node(path, non_color, y):
        node = nodes.new("ShaderNodeTexImage")
        node.image = _load_image(path, non_color)
        node.location = (-560, y)
        node.projection = "BOX"
        node.projection_blend = 0.25
        node.extension = "REPEAT"
        links.new(mapping.outputs["Vector"], node.inputs["Vector"])
        return node

    diffuse = image_node(textures["diffuse"], False, 250)

    colour_out = diffuse.outputs["Color"]
    if "ao" in textures:
        ao_tex = image_node(textures["ao"], True, -50)
        ao_map_mix = nodes.new("ShaderNodeMixRGB")
        ao_map_mix.blend_type = "MULTIPLY"
        ao_map_mix.inputs[0].default_value = 0.6
        ao_map_mix.location = (-320, 200)
        links.new(colour_out, ao_map_mix.inputs[1])
        links.new(ao_tex.outputs["Color"], ao_map_mix.inputs[2])
        colour_out = ao_map_mix.outputs[0]

    # Vertex-colour AO, same contract as the procedural path: an Attribute
    # named "Col" multiplied at 0.35, which is also what tells the glTF
    # exporter to write COLOR_0.
    attr = nodes.new("ShaderNodeAttribute")
    attr.attribute_name = "Col"
    attr.location = (-560, -300)
    ao_mix = nodes.new("ShaderNodeMixRGB")
    ao_mix.blend_type = "MULTIPLY"
    ao_mix.inputs[0].default_value = 0.35
    ao_mix.location = (-80, 150)
    links.new(colour_out, ao_mix.inputs[1])
    links.new(attr.outputs["Color"], ao_mix.inputs[2])
    links.new(ao_mix.outputs[0], principled.inputs["Base Color"])

    if "rough" in textures:
        rough_tex = image_node(textures["rough"], True, 0)
        links.new(rough_tex.outputs["Color"], principled.inputs["Roughness"])
    else:
        principled.inputs["Roughness"].default_value = float(max(0.0, min(1.0, roughness)))

    if "normal" in textures:
        normal_tex = image_node(textures["normal"], True, -250)
        normal_map = nodes.new("ShaderNodeNormalMap")
        normal_map.location = (-320, -250)
        normal_map.inputs["Strength"].default_value = 0.8
        links.new(normal_tex.outputs["Color"], normal_map.inputs["Color"])
        links.new(normal_map.outputs["Normal"], principled.inputs["Normal"])

    if family == "metal_brushed":
        principled.inputs["Metallic"].default_value = 0.85


def make_procedural_material(name: str, family: str, base_color, roughness: float, scale_mm: float):
    """Create a procedural Principled material for `family`.

    No image textures are used -- every variation comes from
    coordinate, mapping, noise, Voronoi or brick nodes so the GLB
    never carries baked images and stays under the 6/25 MiB budgets.
    The graph is slightly visible at render time (grout lines,
    brushed anisotropy, wood grain, plaster mottling) but the
    material stores its flat base colour in ``mat["base_color"]``
    so :func:`prepare_for_gltf_export` can flatten it back to a
    plain Principled before export.

    `scale_mm` controls the mapping scale (e.g. 300 for a 300 mm
    tile, 1000 for a 1 m plaster repeat).
    """
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    # Texture-first (PR TASK-02-04): when the offline cache holds a PBR set for
    # this family, an image-texture graph beats every procedural approximation,
    # so we build that and return. A family with no cached set (glass_clear)
    # falls through to the procedural graph below.
    if _HAS_CACHE and asset_cache is not None:
        try:
            textures = asset_cache.texture_set(family)
        except Exception:
            textures = None
        if textures:
            _build_textured_material(mat, nodes, links, family, textures,
                                     base_color, roughness, scale_mm)
            return mat

    # Keep only Principled BSDF and Output; remove the default stale nodes
    # but preserve those two so we don't have to recreate sockets.
    for n in list(nodes):
        if n.type not in {"BSDF_PRINCIPLED", "OUTPUT_MATERIAL"}:
            nodes.remove(n)
    principled = None
    output = None
    for n in nodes:
        if n.type == "BSDF_PRINCIPLED":
            principled = n
        elif n.type == "OUTPUT_MATERIAL":
            output = n
    if principled is None:
        principled = nodes.new("ShaderNodeBsdfPrincipled")
        principled.location = (0, 0)
    if output is None:
        output = nodes.new("ShaderNodeOutputMaterial")
        output.location = (400, 0)
    # Ensure the output links to the Principled BSDF
    links.new(principled.outputs[0], output.inputs[0])

    # Store the flat fallback for the exporter
    mat["procedural_family"] = family
    mat["base_color"] = (float(base_color[0]), float(base_color[1]), float(base_color[2]), 1.0)

    # Default Principled state (may be overwritten per family)
    principled.inputs["Base Color"].default_value = (float(base_color[0]), float(base_color[1]), float(base_color[2]), 1.0)
    principled.inputs["Roughness"].default_value = float(max(0.0, min(1.0, roughness)))
    # Metallic / Specular defaults are family-specific; keep current unless overwritten
    principled.location = (200, 100)
    output.location = (450, 100)

    # Common helpers: Texture Coordinate + Mapping so every family can
    # drive its texture scale from `scale_mm` without duplicating boilerplate.
    tex_coord = nodes.new("ShaderNodeTexCoord")
    tex_coord.location = (-800, 0)
    mapping = nodes.new("ShaderNodeMapping")
    mapping.location = (-600, 0)
    # scale_mm -> mapping scale: a 300 mm tile should repeat ~3x per metre
    tile_factor = 1000.0 / max(50.0, float(scale_mm))
    # For most families a modest scale keeps the pattern readable; wood
    # grain needs an anisotropic stretch (see below).
    mapping.inputs["Scale"].default_value = (tile_factor, tile_factor, 1.0)
    links.new(tex_coord.outputs["Generated"], mapping.inputs["Vector"])

    # Vertex-colour AO support: if a mesh carries a Col/ AO attribute,
    # the shader multiplies it gently (white = no darkening). The exporter
    # includes the vertex colour layer, costing bytes proportional to
    # vertex count, not to texture resolution.
    try:
        attr = nodes.new("ShaderNodeAttribute")
        attr.attribute_name = "Col"
        attr.location = (-800, -300)
        ao_mix = nodes.new("ShaderNodeMixRGB")
        ao_mix.blend_type = "MULTIPLY"
        ao_mix.inputs[0].default_value = 0.35
        ao_mix.location = (-200, -200)
        # Fac 0.35 means AO darkens at most 35%; missing attribute (white) leaves base unchanged.
        links.new(attr.outputs["Color"], ao_mix.inputs[2])
        # The other mix input will be wired to the family's base-colour chain below.
        # We keep a reference so each family can feed its colour into ao_mix.
    except Exception:
        ao_mix = None  # older Blender; fallback to direct wiring

    # Family-specific procedural graph
    if ao_mix is not None:
        # Initially feed flat colour; each family overwrites ao_mix.inputs[1] when it creates a chain.
        ao_mix.inputs[1].default_value = (float(base_color[0]), float(base_color[1]), float(base_color[2]), 1.0)
        # Principled base colour comes from the AO mix, not directly from the flat colour.
        links.new(ao_mix.outputs[0], principled.inputs["Base Color"])

    if family == "plaster_painted":
        noise = nodes.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value = 4.0
        noise.inputs["Detail"].default_value = 2.0
        noise.inputs["Roughness"].default_value = 0.6
        noise.location = (-400, 100)
        links.new(mapping.outputs["Vector"], noise.inputs["Vector"])
        ramp = nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].color = (0.92, 0.92, 0.92, 1.0)
        ramp.color_ramp.elements[0].position = 0.35
        ramp.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)
        ramp.color_ramp.elements[1].position = 0.65
        ramp.location = (-200, 100)
        links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
        mix = nodes.new("ShaderNodeMixRGB")
        mix.blend_type = "MIX"
        mix.inputs[0].default_value = 0.14
        mix.location = (-40, 80)
        mix.inputs[1].default_value = (float(base_color[0]), float(base_color[1]), float(base_color[2]), 1.0)
        links.new(ramp.outputs["Color"], mix.inputs[2])
        if ao_mix is not None:
            ao_mix.inputs[1].default_value = (float(base_color[0]), float(base_color[1]), float(base_color[2]), 1.0)
            links.new(mix.outputs[0], ao_mix.inputs[1])
        else:
            links.new(mix.outputs[0], principled.inputs["Base Color"])
        # Micro-surface bump: noise drives a low-strength Bump so walls are not
        # flat 255/255/255 in glancing light (the Bar's stone+plaster dapple).
        try:
            bump = nodes.new("ShaderNodeBump")
            bump.inputs["Strength"].default_value = 0.22
            bump.inputs["Distance"].default_value = 0.3
            bump.location = (-40, -100)
            links.new(noise.outputs["Fac"], bump.inputs["Height"])
            links.new(bump.outputs["Normal"], principled.inputs["Normal"])
        except Exception:
            pass
    elif family == "ceramic_tile":
        brick = nodes.new("ShaderNodeTexBrick")
        # Tile dimensions drive brick width/height via mapping; brick node's own
        # Mortar/Grout thickness is what makes the grout visible.
        brick.inputs["Scale"].default_value = 4.0
        brick.inputs["Mortar Size"].default_value = 0.025
        brick.inputs["Brick Width"].default_value = 0.5
        brick.inputs["Row Height"].default_value = 0.5
        brick.location = (-400, 100)
        links.new(mapping.outputs["Vector"], brick.inputs["Vector"])
        # Grout vs tile colour -- tile uses base_color, grout a slightly darker grey
        grout_col = (max(0.0, base_color[0] * 0.78), max(0.0, base_color[1] * 0.78), max(0.0, base_color[2] * 0.78), 1.0)
        # Brick node outputs Color (tile) and Fac (mortar mask). Use a Mix to show grout.
        # Instead of wiring Fac->Colour directly (brick already does), tint mortar via the node's inputs.
        brick.inputs["Mortar"].default_value = grout_col  # type: ignore[attr-defined]
        brick.inputs["Color1"].default_value = (float(base_color[0]), float(base_color[1]), float(base_color[2]), 1.0)  # type: ignore[attr-defined]
        brick.inputs["Color2"].default_value = (float(base_color[0]) * 0.96, float(base_color[1]) * 0.96, float(base_color[2]) * 0.96, 1.0)  # type: ignore[attr-defined]
        if ao_mix is not None:
            links.new(brick.outputs["Color"], ao_mix.inputs[1])
        else:
            links.new(brick.outputs["Color"], principled.inputs["Base Color"])
        principled.inputs["Roughness"].default_value = float(max(0.08, min(1.0, roughness * 0.7)))

    elif family == "stone_slab":
        vor = nodes.new("ShaderNodeTexVoronoi")
        vor.inputs["Scale"].default_value = 6.0
        try:
            vor.feature = "SMOOTH_F1"  # type: ignore[attr-defined]
        except Exception:
            pass
        vor.location = (-400, 100)
        links.new(mapping.outputs["Vector"], vor.inputs["Vector"])
        noise = nodes.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value = 3.0
        noise.location = (-400, -100)
        links.new(mapping.outputs["Vector"], noise.inputs["Vector"])
        mix = nodes.new("ShaderNodeMixRGB")
        mix.blend_type = "MIX"
        mix.inputs[0].default_value = 0.55
        mix.location = (-200, 40)
        links.new(vor.outputs["Distance"], mix.inputs[0])
        mix.inputs[1].default_value = (float(base_color[0]), float(base_color[1]), float(base_color[2]), 1.0)
        # Slight darker mottling
        darker = (base_color[0] * 0.88, base_color[1] * 0.88, base_color[2] * 0.88, 1.0)
        mix.inputs[2].default_value = darker
        if ao_mix is not None:
            links.new(mix.outputs[0], ao_mix.inputs[1])
        else:
            links.new(mix.outputs[0], principled.inputs["Base Color"])
        try:
            bump = nodes.new("ShaderNodeBump")
            bump.inputs["Strength"].default_value = 0.35
            bump.location = (-40, -80)
            links.new(noise.outputs["Fac"], bump.inputs["Height"])
            links.new(bump.outputs["Normal"], principled.inputs["Normal"])
        except Exception:
            pass

    elif family == "wood_board":
        # Anisotropic grain: stretch mapping on X so noise bands like wood
        mapping.inputs["Scale"].default_value = (tile_factor * 0.25, tile_factor * 2.0, 1.0)
        noise = nodes.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value = 2.5
        noise.inputs["Detail"].default_value = 3.0
        noise.location = (-400, 100)
        links.new(mapping.outputs["Vector"], noise.inputs["Vector"])
        ramp = nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].color = (float(base_color[0]) * 0.85, float(base_color[1]) * 0.78, float(base_color[2]) * 0.70, 1.0)
        ramp.color_ramp.elements[1].color = (float(base_color[0]), float(base_color[1]), float(base_color[2]), 1.0)
        ramp.location = (-200, 100)
        links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
        if ao_mix is not None:
            links.new(ramp.outputs["Color"], ao_mix.inputs[1])
        else:
            links.new(ramp.outputs["Color"], principled.inputs["Base Color"])
        principled.inputs["Roughness"].default_value = float(max(0.25, min(1.0, roughness)))
        try:
            principled.inputs["Anisotropic"].default_value = 0.55
            principled.inputs["Anisotropic Rotation"].default_value = 0.25
        except Exception:
            pass

    elif family == "metal_brushed":
        # Brushed streaks: high-frequency noise stretched strongly on one axis
        mapping.inputs["Scale"].default_value = (tile_factor * 4.0, tile_factor * 0.2, 1.0)
        noise = nodes.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value = 8.0
        noise.inputs["Detail"].default_value = 2.0
        noise.location = (-400, 100)
        links.new(mapping.outputs["Vector"], noise.inputs["Vector"])
        # Modulate roughness so brushing reads as subtle highlight variation
        ramp = nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].color = (0.15, 0.15, 0.15, 1.0)
        ramp.color_ramp.elements[1].color = (0.45, 0.45, 0.45, 1.0)
        ramp.location = (-200, 0)
        links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
        # Keep base colour but make the metal visibly anisotropic
        if ao_mix is not None:
            # Metal colour stays flat; brushing affects roughness/anisotropy only.
            pass
        principled.inputs["Metallic"].default_value = 0.85
        principled.inputs["Roughness"].default_value = 0.18
        try:
            principled.inputs["Anisotropic"].default_value = 0.75
            principled.inputs["Anisotropic Rotation"].default_value = 0.5
        except Exception:
            pass

    elif family == "glass_clear":
        principled.inputs["Base Color"].default_value = (float(base_color[0]), float(base_color[1]), float(base_color[2]), 1.0)
        principled.inputs["Roughness"].default_value = 0.04
        principled.inputs["Metallic"].default_value = 0.0
        try:
            if "Transmission Weight" in principled.inputs:
                principled.inputs["Transmission Weight"].default_value = 0.98
            elif "Transmission" in principled.inputs:
                principled.inputs["Transmission"].default_value = 0.98
            if "IOR" in principled.inputs:
                principled.inputs["IOR"].default_value = 1.45
            if "Alpha" in principled.inputs:
                principled.inputs["Alpha"].default_value = 0.35
        except Exception:
            pass
        if ao_mix is not None:
            # Glass shouldn't be darkened by AO; disconnect the AO mix for glass.
            try:
                links.new(principled.inputs["Base Color"].links[0].from_socket, principled.inputs["Base Color"])  # no-op
            except Exception:
                pass
            # Rewire Principled base directly so AO doesn't tint glass
            ao_mix.inputs[0].default_value = 0.0

    elif family == "concrete_formed":
        noise = nodes.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value = 1.8
        noise.inputs["Detail"].default_value = 2.0
        noise.location = (-400, 100)
        links.new(mapping.outputs["Vector"], noise.inputs["Vector"])
        vor = nodes.new("ShaderNodeTexVoronoi")
        vor.inputs["Scale"].default_value = 12.0
        vor.location = (-400, -120)
        links.new(mapping.outputs["Vector"], vor.inputs["Vector"])
        mix = nodes.new("ShaderNodeMixRGB")
        mix.blend_type = "MIX"
        mix.inputs[0].default_value = 0.35
        mix.location = (-200, 40)
        mix.inputs[1].default_value = (float(base_color[0]), float(base_color[1]), float(base_color[2]), 1.0)
        darker = (base_color[0] * 0.92, base_color[1] * 0.92, base_color[2] * 0.92, 1.0)
        mix.inputs[2].default_value = darker
        links.new(vor.outputs["Distance"], mix.inputs[0])
        if ao_mix is not None:
            links.new(mix.outputs[0], ao_mix.inputs[1])
        else:
            links.new(mix.outputs[0], principled.inputs["Base Color"])
        try:
            bump = nodes.new("ShaderNodeBump")
            bump.inputs["Strength"].default_value = 0.5
            bump.location = (-40, -80)
            links.new(noise.outputs["Fac"], bump.inputs["Height"])
            links.new(bump.outputs["Normal"], principled.inputs["Normal"])
        except Exception:
            pass
        principled.inputs["Roughness"].default_value = 0.82

    else:
        # Fallback: keep flat
        pass

    return mat


def prepare_for_gltf_export(keep_textures: bool = True) -> None:
    """Flatten procedural graphs but keep vertex-colour AO so the GLB carries it.

    The render uses the full procedural graph (grout, noise, anisotropy) but a
    node graph cannot be exported, so every procedural chain is flattened to
    the material's stored base colour plus a ``Col`` vertex layer multiplied
    into Base Color (strength 0.35).

    Materials built from the cached CC0 PBR sets are different: an image
    texture *is* exportable, and carrying it is the whole point of the full
    build. With ``keep_textures`` (the default) those materials are left
    intact. Pass ``keep_textures=False`` for the light phone build, where the
    6 MiB budget cannot afford image data and the flat colour plus vertex AO
    has to stand in for it.
    """
    for mat in list(bpy.data.materials):
        if not mat.use_nodes or mat.node_tree is None:
            continue
        base = mat.get("base_color")
        if base is None:
            continue
        if (mat.get("textured") or mat.get("lightmapped")) and keep_textures:
            # An exportable image-texture graph: leave it exactly as built.
            continue
        ntree = mat.node_tree
        principled = ntree.nodes.get("Principled BSDF")
        if principled is None:
            for n in ntree.nodes:
                if n.type == "BSDF_PRINCIPLED":
                    principled = n
                    break
        if principled is None:
            continue
        # Identify the AO multiply node (our make_procedural_material creates
        # a Multiply MixRGB with inputs[0]==0.35 fed by an Attribute "Col").
        ao_mix = None
        attr_node = None
        for n in ntree.nodes:
            if n.type == "ATTRIBUTE" and getattr(n, "attribute_name", "") == "Col":
                attr_node = n
            if n.type == "MIX_RGB" and n.blend_type == "MULTIPLY":
                try:
                    if abs(float(n.inputs[0].default_value) - 0.35) < 1e-6:
                        ao_mix = n
                except Exception:
                    pass
        # Keep only the AO chain into Base Color; sever procedural chains
        # upstream of ao_mix.inputs[1] (the procedural colour) and flatten that
        # input to the stored flat base colour. The link ao_mix -> Principled
        # is intentionally preserved so the exporter sees the Attribute usage
        # and writes COLOR_0.
        if ao_mix is not None and principled.inputs.get("Base Color") is not None:
            # Sever procedural link into ao_mix's colour input, flatten to base
            try:
                for link in list(ao_mix.inputs[1].links):
                    ntree.links.remove(link)
                ao_mix.inputs[1].default_value = tuple(base)  # type: ignore[arg-type]
            except Exception:
                pass
            # Ensure Principled Base Color stays linked through ao_mix
            # (don't remove that link). Remove other Base Color links only if
            # they are NOT from ao_mix.
            for link in list(principled.inputs["Base Color"].links):
                if link.from_node != ao_mix:
                    ntree.links.remove(link)
        else:
            # No AO chain (e.g. glass) -- flatten Base Color fully
            for link in list(principled.inputs["Base Color"].links):
                ntree.links.remove(link)
            try:
                principled.inputs["Base Color"].default_value = tuple(base)  # type: ignore[arg-type]
            except Exception:
                pass
        # Clamp roughness/metallic, sever procedural links into them
        for inp_name in ("Roughness", "Metallic", "Normal", "Anisotropic", "Anisotropic Rotation"):
            try:
                inp = principled.inputs.get(inp_name)
                if inp is not None:
                    for link in list(inp.links):
                        ntree.links.remove(link)
            except Exception:
                continue
        try:
            r = float(principled.inputs["Roughness"].default_value)
            if r < 0.08:
                r = 0.18
            if r > 0.98:
                r = 0.98
            principled.inputs["Roughness"].default_value = r
        except Exception:
            pass
        try:
            m = float(principled.inputs["Metallic"].default_value)
            if m > 0.8:
                m = 0.5
            principled.inputs["Metallic"].default_value = m
        except Exception:
            pass
        # Strip non-essential procedural nodes but keep the AO chain and the
        # Principled + Output so the file stays tiny.
        keep_types = {"OUTPUT_MATERIAL", "BSDF_PRINCIPLED"}
        keep_names = {principled.name, "Material Output"}
        if ao_mix is not None:
            keep_names.add(ao_mix.name)
        if attr_node is not None:
            keep_names.add(attr_node.name)
        for n in list(ntree.nodes):
            if n.name in keep_names or n.type in keep_types:
                continue
            # Keep the AO Attribute/Mix pair even if name differs slightly
            if n.type in {"ATTRIBUTE", "MIX_RGB"} and n.name in keep_names:
                continue
            try:
                ntree.nodes.remove(n)
            except Exception:
                pass

def bake_lightmap(resolution: int = 256, max_objects: int = 400,
                  samples: int = 24) -> int:
    """Bake combined direct+indirect light to a per-object texture (PR TASK-05-04).

    The GLB the viewer serves has no global illumination of its own — three.js
    gives it one hemisphere light and one directional. Baking the Cycles
    solution into an image and multiplying it into Base Color carries the
    render's bounce light, soft shadows and colour bleed into the viewer, which
    is the single biggest gap between the still and the interactive model.

    Returns the number of objects baked. Every step is guarded: baking is an
    enhancement, and a scene that cannot be baked must still export.

    This is CPU-bound (see the hardware note in `lessons.md` — there is no GPU
    render path on the reference machine), hence `max_objects` and the low
    default sample count. Call it before `prepare_for_gltf_export`.
    """
    scene = bpy.context.scene
    meshes = [o for o in scene.objects
              if o.type == "MESH" and o.data is not None and len(o.data.polygons) > 0]
    if not meshes:
        return 0
    if len(meshes) > max_objects:
        # Bake the largest surfaces, where indirect light actually reads, and
        # leave the small props to the vertex-colour AO layer.
        meshes.sort(key=lambda o: -sum(p.area for p in o.data.polygons))
        meshes = meshes[:max_objects]

    previous_engine = scene.render.engine
    try:
        scene.render.engine = "CYCLES"
    except TypeError:
        return 0
    previous_samples = getattr(scene.cycles, "samples", None)
    scene.cycles.samples = samples
    try:
        scene.cycles.device = "CPU"
    except Exception:
        pass

    baked = 0
    for obj in meshes:
        try:
            mesh = obj.data
            if not mesh.materials or all(m is None for m in mesh.materials):
                continue
            # A dedicated second UV layer: the material's own UVs are tiled for
            # texture repeat, which a lightmap must never be.
            if "Lightmap" in mesh.uv_layers:
                mesh.uv_layers["Lightmap"].active = True
            else:
                mesh.uv_layers.new(name="Lightmap")
            mesh.uv_layers.active = mesh.uv_layers["Lightmap"]

            bpy.ops.object.select_all(action="DESELECT")
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_all(action="SELECT")
            bpy.ops.uv.smart_project(angle_limit=1.15, island_margin=0.02)
            bpy.ops.object.mode_set(mode="OBJECT")

            image = bpy.data.images.new(
                f"lightmap_{obj.name}", width=resolution, height=resolution,
                float_buffer=False,
            )
            targets = []
            for material in mesh.materials:
                if material is None or not material.use_nodes:
                    continue
                nodes = material.node_tree.nodes
                node = nodes.new("ShaderNodeTexImage")
                node.image = image
                node.label = "Lightmap"
                node.location = (-1400, 400)
                nodes.active = node
                targets.append((material, node))
            if not targets:
                bpy.data.images.remove(image)
                continue

            bpy.ops.object.bake(type="COMBINED", use_clear=True, margin=2)

            # Multiply the baked light into Base Color so the exported GLB
            # carries it as ordinary texture data.
            for material, node in targets:
                _wire_lightmap(material, node)
            obj["lightmap"] = image.name
            baked += 1
        except Exception as exc:
            print(f"lightmap bake skipped for {obj.name}: {exc}")
            try:
                if bpy.context.object and bpy.context.object.mode != "OBJECT":
                    bpy.ops.object.mode_set(mode="OBJECT")
            except Exception:
                pass

    scene.render.engine = previous_engine
    if previous_samples is not None:
        scene.cycles.samples = previous_samples
    print(f"lightmap: baked {baked}/{len(meshes)} objects at {resolution}px")
    return baked


def _wire_lightmap(material, tex_node) -> None:
    """Multiply a baked lightmap into a material's Base Color chain."""
    tree = material.node_tree
    principled = None
    for node in tree.nodes:
        if node.type == "BSDF_PRINCIPLED":
            principled = node
            break
    if principled is None:
        return
    base = principled.inputs.get("Base Color")
    if base is None:
        return

    uv = tree.nodes.new("ShaderNodeUVMap")
    uv.uv_map = "Lightmap"
    uv.location = (-1600, 400)
    tree.links.new(uv.outputs["UV"], tex_node.inputs["Vector"])

    mix = tree.nodes.new("ShaderNodeMixRGB")
    mix.blend_type = "MULTIPLY"
    mix.inputs[0].default_value = 1.0
    mix.location = (60, 300)

    existing = list(base.links)
    if existing:
        source = existing[0].from_socket
        tree.links.remove(existing[0])
        tree.links.new(source, mix.inputs[1])
    else:
        mix.inputs[1].default_value = base.default_value
    tree.links.new(tex_node.outputs["Color"], mix.inputs[2])
    tree.links.new(mix.outputs[0], base)
    material["lightmapped"] = True


def add_vertex_color_ao(strength: float = 0.52) -> None:
    """Add a per-mesh ``Col`` vertex-colour layer that encodes stacked-jardinière AO.

    * Deep soffits: vertices on the underside of a mesh (normal facing -Z)
      or near the bottom of their local bound are driven toward near-black
      (0.22), giving the 25-layer Stacking Green Jardinière shadow. The
      strength is intentionally harsh so it survives the viewer's 0.35 multiply.
    * Leaf dapple: a hash of vertex index + world XY adds mottled 4-7 %
      occlusion like sun through planters.
    * Formwork lines: horizontal bands every ~0.6 m of world height are
      3 % darker, like shuttering.
    * Pitted variation: a second hash adds 2-4 % warm noise for concrete.
    No image textures are created; cost scales with vertex count, so the
    6/25 MiB budgets remain achievable.
    """
    for obj in list(bpy.data.objects):
        if obj.type != "MESH" or obj.data is None:
            continue
        mesh = obj.data
        try:
            if "Col" not in mesh.attributes:
                mesh.attributes.new(name="Col", type="FLOAT_COLOR", domain="CORNER")
        except Exception:
            try:
                if "Col" not in mesh.vertex_colors:
                    mesh.vertex_colors.new(name="Col")
            except Exception:
                continue
        try:
            layer = mesh.attributes.get("Col")
            if layer is None:
                continue
            data = layer.data
            data = layer.data
        except Exception:
            try:
                layer = mesh.vertex_colors.get("Col")
                data = layer.data if layer is not None else None
            except Exception:
                continue
        if data is None:
            continue
        # Compute per-loop AO factor with jardinière depth, dapple, formwork
        try:
            z_vals = [obj.matrix_world @ v.co for v in mesh.vertices]
            if not z_vals:
                continue
            z_min = min(v.z for v in z_vals)
            z_max = max(v.z for v in z_vals)
            z_span = max(0.4, z_max - z_min)
        except Exception:
            z_min, z_span = 0.0, 5.0
        try:
            for loop in mesh.loops:
                v = mesh.vertices[loop.vertex_index]
                world_co = obj.matrix_world @ v.co
                world_z = world_co.z
                world_x = world_co.x
                world_y = world_co.y
                # Height bias: deep soffit (bottom) -> near-black 0.22, top -> 1.0
                h = 1.0 - max(0.0, min(1.0, (world_z - z_min) / z_span)) * 0.60
                # Underside bias: if mesh is a slab/balcony, its bottom loops are darker
                # We approximate by world_z near z_min and object Z span small (<0.5m) => slab
                is_slab = z_span < 0.45
                if is_slab and world_z < z_min + 0.08:
                    dark_base = 0.22
                else:
                    dark_base = 1.0 - strength * h * 1.05
                dark = dark_base
                # Formwork lines: horizontal shuttering every ~0.6 m
                form_band = int(world_z * 1.666) % 7  # 0.6m period
                if form_band == 0:
                    dark -= 0.03
                elif form_band == 3:
                    dark -= 0.015
                # Leaf-dappled occlusion: mottled spots like sun through planters
                # Hash from world XY + index gives pseudo-random but coherent islands
                dapple_hash = (int(world_x * 3.7) * 13 + int(world_y * 3.7) * 7 + loop.vertex_index * 17) % 53
                if dapple_hash < 7:
                    dark -= 0.065
                elif dapple_hash < 14:
                    dark -= 0.035
                # Pitted concrete variation: warm noise on wall faces
                pit_hash = (loop.vertex_index * 37 + int(world_z * 9.3)) % 19
                dark += (pit_hash - 9) / 19.0 * 0.025
                dark = max(0.22, min(1.0, dark))
                try:
                    data[loop.index].color = (dark, dark, dark, 1.0)
                except Exception:
                    try:
                        data[loop.index].color_srgb = (dark, dark, dark, 1.0)  # type: ignore[attr-defined]
                    except Exception:
                        pass
        except Exception:
            continue
            continue

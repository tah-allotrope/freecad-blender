"""Principled-BSDF material definitions, keyed by style. Runs inside Blender."""

import bpy

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
# ceramic tile with grout.
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


def get_material(style: str, key: str) -> "bpy.types.Material":
    """Return a cached Principled material for a palette key.

    When the key maps to a procedural family we delegate to
    :func:`make_procedural_material` so the render shows grout/noise/
    anisotropy while the glTF export still carries only a flat base
    colour (see :func:`prepare_for_gltf_export`).
    """
    cache_key = f"{style}:{key}"
    if cache_key in _cache:
        return _cache[cache_key]
    palette = PALETTES.get(style, PALETTES["modern-minimal"])
    spec = palette.get(key, palette["furniture"])
    family = _FAMILY_FOR_KEY.get(key, "plaster_painted")
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


def prepare_for_gltf_export() -> None:
    """Flatten procedural graphs but keep vertex-colour AO so the GLB carries it.

    The render uses the full procedural graph (grout, noise, anisotropy) but
    the GLB should contain only flat base colours plus a ``Col`` vertex
    layer multiplied into Base Color (strength 0.35). This keeps the file tiny
    (no image textures) while giving the viewer the deep soffit shadows and
    leaf-dappled occlusion that separate a maquette from Stacking Green.
    """
    for mat in list(bpy.data.materials):
        if not mat.use_nodes or mat.node_tree is None:
            continue
        base = mat.get("base_color")
        if base is None:
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

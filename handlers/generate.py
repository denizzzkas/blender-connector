import uuid
import json
import time
import math

BLENDER_PROMPT_TEMPLATE = """You are an expert Blender Python (bpy) developer.
Generate a clean, robust, standalone Python script using Blender's `bpy` module based on the user's prompt.

USER PROMPT: {prompt}
TARGET MODE: {target_mode}

RULES:
1. Always import `bpy`, `math`, `random` if needed.
2. If TARGET MODE is 'new_scene', clear default objects first.
3. Ensure objects are created with proper shading and materials (use_nodes=True).
4. Create camera and studio lighting if building a full scene.
5. Return clean executable code without markdown tags.
6. Ensure script runs cleanly in Blender 3.0+ without errors.
"""

def generate_bpy_code(prompt: str, target_mode: str = "new_scene") -> tuple[str, str]:
    """
    Generates dynamic Blender Python (bpy) code tailored to the user's prompt.
    Returns (code_string, explanation).
    """
    prompt_lower = prompt.lower()
    is_beside = any(w in prompt_lower for w in ["рядом", "beside", "next to", "alongside", "справа", "слева"]) or target_mode == "modify_active"

    code_lines = [
        "import bpy",
        "import math",
        "import random",
        "",
        "# Imperal AI Generated Blender Script",
        f"# Prompt: {prompt}",
        f"# Mode: {target_mode}",
        "",
        "# 0. Ensure safe OBJECT mode",
        "if bpy.context.object and getattr(bpy.context.object, 'mode', 'OBJECT') != 'OBJECT':",
        "    try: bpy.ops.object.mode_set(mode='OBJECT')",
        "    except Exception: pass",
        ""
    ]

    if target_mode == "new_scene" and not is_beside:
        code_lines.extend([
            "# Clear all existing objects in scene",
            "for obj in list(bpy.context.scene.objects):",
            "    bpy.data.objects.remove(obj, do_unlink=True)",
            ""
        ])

    # Dynamic Bounding Box Offset for placing beside existing objects
    if is_beside:
        code_lines.extend([
            "# Calculate bounding box offset to place geometry beside existing objects",
            "all_objs = [o for o in bpy.context.scene.objects if o.type in ('MESH', 'CURVE', 'SURFACE')]",
            "if all_objs:",
            "    max_x = max([(o.matrix_world @ mathutils.Vector(corner)).x for o in all_objs for corner in o.bound_box]) if hasattr(bpy, 'mathutils') else max([o.location.x + max(o.dimensions.x, 2.0) for o in all_objs])",
            "    offset_x = max_x + 5.0",
            "else:",
            "    offset_x = 10.0",
            ""
        ])
    else:
        code_lines.append("offset_x = 0.0\n")

    # Helper function inside script for creating Principled BSDF materials
    code_lines.extend([
        "# Material helper",
        "def create_material(name, color=(0.8, 0.8, 0.8, 1.0), metallic=0.0, roughness=0.5, emission=None, emission_strength=1.0):",
        "    mat = bpy.data.materials.new(name=name)",
        "    mat.use_nodes = True",
        "    bsdf = mat.node_tree.nodes.get('Principled BSDF')",
        "    if bsdf:",
        "        if 'Base Color' in bsdf.inputs: bsdf.inputs['Base Color'].default_value = color",
        "        if 'Metallic' in bsdf.inputs: bsdf.inputs['Metallic'].default_value = metallic",
        "        if 'Roughness' in bsdf.inputs: bsdf.inputs['Roughness'].default_value = roughness",
        "        if emission:",
        "            if 'Emission Color' in bsdf.inputs: bsdf.inputs['Emission Color'].default_value = emission",
        "            elif 'Emission' in bsdf.inputs: bsdf.inputs['Emission'].default_value = emission",
        "            if 'Emission Strength' in bsdf.inputs: bsdf.inputs['Emission Strength'].default_value = emission_strength",
        "    return mat",
        ""
    ])

    # Pattern Matching for Target Geometry
    if "cube" in prompt_lower or "box" in prompt_lower:
        color = "(0.9, 0.47, 0.16, 1.0)" if "orange" in prompt_lower or "imperal" in prompt_lower else "(0.1, 0.5, 0.9, 1.0)"
        metallic = "0.9" if "metal" in prompt_lower else "0.1"
        roughness = "0.1" if "gloss" in prompt_lower or "metal" in prompt_lower else "0.4"
        code_lines.extend([
            f"mat = create_material('Cube_Mat', color={color}, metallic={metallic}, roughness={roughness})",
            "bpy.ops.mesh.primitive_cube_add(size=2.0, location=(offset_x, 0, 1.0))",
            "cube = bpy.context.active_object",
            "cube.name = 'Imperal_Cube'",
            "cube.data.materials.append(mat)",
        ])
        explanation = f"Created a procedural cube at location offset ({color})."

    elif "sphere" in prompt_lower or "planet" in prompt_lower or "ball" in prompt_lower:
        color = "(0.1, 0.6, 0.9, 1.0)" if "blue" in prompt_lower else "(0.85, 0.2, 0.2, 1.0)"
        metallic = "0.9" if "metal" in prompt_lower else "0.0"
        code_lines.extend([
            f"mat = create_material('Sphere_Mat', color={color}, metallic={metallic}, roughness=0.15)",
            "bpy.ops.mesh.primitive_uv_sphere_add(radius=1.5, location=(offset_x, 0, 1.5))",
            "sphere = bpy.context.active_object",
            "sphere.name = 'Imperal_Sphere'",
            "bpy.ops.object.shade_smooth()",
            "sphere.data.materials.append(mat)",
        ])
        explanation = "Created a smooth procedural sphere with reflections."

    elif "cylinder" in prompt_lower or "tube" in prompt_lower or "pillar" in prompt_lower:
        code_lines.extend([
            "mat = create_material('Cylinder_Mat', color=(0.2, 0.8, 0.4, 1.0), roughness=0.3)",
            "bpy.ops.mesh.primitive_cylinder_add(radius=1.0, depth=3.0, location=(offset_x, 0, 1.5))",
            "cylinder = bpy.context.active_object",
            "cylinder.name = 'Imperal_Cylinder'",
            "cylinder.data.materials.append(mat)",
        ])
        explanation = "Created a procedural cylinder with material."

    elif "crystal" in prompt_lower or "gem" in prompt_lower or "shard" in prompt_lower or "cluster" in prompt_lower or "magic" in prompt_lower:
        code_lines.extend([
            "# Rocky Base",
            "mat_rock = create_material('Dark_Rock_Mat', color=(0.05, 0.04, 0.07, 1.0), roughness=0.9)",
            "bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=3.5, depth=0.4, location=(offset_x, 0, -0.2))",
            "base = bpy.context.active_object",
            "base.name = 'Dark_Rock_Base'",
            "base.data.materials.append(mat_rock)",
            "",
            "# Central Crystal",
            "mat_crystal = create_material('Bioluminescent_Crystal', color=(0.85, 0.05, 0.65, 1.0), roughness=0.1, metallic=0.2, emission=(0.9, 0.1, 0.7, 1.0), emission_strength=4.0)",
            "bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.9, depth=3.2, location=(offset_x, 0, 1.6))",
            "main_crystal = bpy.context.active_object",
            "main_crystal.name = 'Main_Crystal'",
            "main_crystal.data.materials.append(mat_crystal)",
            "",
            "# Shards",
            "random.seed(42)",
            "for i in range(6):",
            "    ang = (2 * math.pi / 6) * i + random.uniform(-0.15, 0.15)",
            "    dist = random.uniform(1.3, 2.0)",
            "    x, y = offset_x + math.cos(ang) * dist, math.sin(ang) * dist",
            "    h = random.uniform(1.2, 2.2)",
            "    bpy.ops.mesh.primitive_cone_add(vertices=5, radius1=0.35, depth=h, location=(x, y, h / 2.0))",
            "    shard = bpy.context.active_object",
            "    shard.name = f'Crystal_Shard_{i+1}'",
            "    shard.data.materials.append(mat_crystal)",
            "",
            "# Inner Glow Lights",
            "bpy.ops.object.light_add(type='POINT', location=(offset_x, 0, 2.0))",
            "glow = bpy.context.active_object",
            "glow.data.color = (1.0, 0.1, 0.8)",
            "glow.data.energy = 120.0",
        ])
        explanation = "Created a procedural glowing bioluminescent crystal cluster on rock terrain."

    elif any(w in prompt_lower for w in ["city", "building", "town", "street"]):
        code_lines.extend([
            "# Procedural City Grid",
            "mat_bldg = create_material('Building_Mat', color=(0.2, 0.25, 0.3, 1.0), roughness=0.3, metallic=0.5)",
            "for ix in range(-2, 3):",
            "    for iy in range(-2, 3):",
            "        bh = random.uniform(1.5, 6.0)",
            "        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(offset_x + ix * 2.0, iy * 2.0, bh / 2.0))",
            "        bldg = bpy.context.active_object",
            "        bldg.scale = (1.2, 1.2, bh)",
            "        bldg.data.materials.append(mat_bldg)",
        ])
        explanation = "Generated a 5x5 procedural city grid with random building heights."

    elif any(w in prompt_lower for w in ["room", "set", "movie", "film", "fireplace", "комнат", "сцена", "площадк", "камин", "актер", "съемк"]):
        code_lines.extend([
            "# ==========================================================================",
            "# SCENE 3: Comprehensive Film Set Reproduction from Reference",
            "# ==========================================================================",
            "import mathutils",
            "",
            "# Calculate precise X offset (align with previous 22m grid spacing)",
            "all_objs = [o for o in bpy.context.scene.objects if o.type in ('MESH', 'CURVE', 'SURFACE')]",
            "if all_objs:",
            "    max_x = max([o.location.x for o in all_objs])",
            "    offset_x = round(max_x / 22.0 + 1) * 22.0 if max_x > 5 else 22.0",
            "else:",
            "    offset_x = 0.0",
            "",
            "# 1. Materials Setup",
            "mat_wood_floor = create_material('Wood_Floor_Mat_3', color=(0.22, 0.12, 0.06, 1.0), roughness=0.3)",
            "mat_wall = create_material('Classic_Wall_Mat_3', color=(0.14, 0.16, 0.20, 1.0), roughness=0.75)",
            "mat_stone = create_material('Fireplace_Stone_3', color=(0.82, 0.80, 0.75, 1.0), roughness=0.4)",
            "mat_dark_hearth = create_material('Hearth_Dark_3', color=(0.04, 0.03, 0.03, 1.0), roughness=0.9)",
            "mat_gold = create_material('Gold_Frame_3', color=(0.85, 0.68, 0.18, 1.0), metallic=0.9, roughness=0.2)",
            "mat_red_velvet = create_material('Armchair_Red_Velvet_3', color=(0.50, 0.06, 0.10, 1.0), roughness=0.8)",
            "mat_gear = create_material('Matte_Black_Gear_3', color=(0.03, 0.03, 0.03, 1.0), metallic=0.7, roughness=0.3)",
            "mat_skin = create_material('Actor_Skin_3', color=(0.85, 0.65, 0.52, 1.0), roughness=0.6)",
            "mat_yellow_dress = create_material('Dress_Yellow_3', color=(0.95, 0.75, 0.05, 1.0), roughness=0.5)",
            "mat_crew = create_material('Crew_Clothes_3', color=(0.10, 0.10, 0.12, 1.0), roughness=0.7)",
            "",
            "# 2. Room Geometry (Floor & Walls)",
            "bpy.ops.mesh.primitive_plane_add(size=10, location=(offset_x, 0, 0))",
            "floor = bpy.context.active_object; floor.name = 'Wood_Floor.002'; floor.scale = (1.0, 1.2, 1.0); floor.data.materials.append(mat_wood_floor)",
            "",
            "bpy.ops.mesh.primitive_cube_add(size=1, location=(offset_x, 5.0, 3.0))",
            "w_back = bpy.context.active_object; w_back.name = 'Wall_Back.002'; w_back.scale = (12.0, 0.2, 6.0); w_back.data.materials.append(mat_wall)",
            "",
            "bpy.ops.mesh.primitive_cube_add(size=1, location=(offset_x - 6.0, 0, 3.0))",
            "w_left = bpy.context.active_object; w_left.name = 'Wall_Left.002'; w_left.scale = (0.2, 10.0, 6.0); w_left.data.materials.append(mat_wall)",
            "",
            "# 3. Ornate Fireplace & Hearth",
            "bpy.ops.mesh.primitive_cube_add(size=1, location=(offset_x, 4.7, 1.2))",
            "fp_surround = bpy.context.active_object; fp_surround.name = 'Fireplace_Surround.002'; fp_surround.scale = (3.2, 0.6, 2.4); fp_surround.data.materials.append(mat_stone)",
            "",
            "bpy.ops.mesh.primitive_cube_add(size=1, location=(offset_x, 4.5, 0.9))",
            "fp_hearth = bpy.context.active_object; fp_hearth.name = 'Fireplace_Hearth.002'; fp_hearth.scale = (1.8, 0.5, 1.6); fp_hearth.data.materials.append(mat_dark_hearth)",
            "",
            "bpy.ops.mesh.primitive_cube_add(size=1, location=(offset_x, 4.6, 2.5))",
            "fp_mantel = bpy.context.active_object; fp_mantel.name = 'Fireplace_Mantel.002'; fp_mantel.scale = (3.6, 0.8, 0.2); fp_mantel.data.materials.append(mat_stone)",
            "",
            "# Warm Fireplace Glow Light",
            "bpy.ops.object.light_add(type='POINT', location=(offset_x, 4.3, 0.8))",
            "fire_light = bpy.context.active_object; fire_light.name = 'Fire_Glow_Light.002'",
            "fire_light.data.color = (1.0, 0.42, 0.10); fire_light.data.energy = 85.0",
            "",
            "# Gold Picture Frame above Mantel",
            "bpy.ops.mesh.primitive_cube_add(size=1, location=(offset_x, 4.8, 3.8))",
            "frame = bpy.context.active_object; frame.name = 'Fireplace_Painting_Frame.002'; frame.scale = (2.2, 0.1, 1.5); frame.data.materials.append(mat_gold)",
            "",
            "# 4. Dialogue Area (Armchairs & Coffee Table)",
            "bpy.ops.mesh.primitive_cube_add(size=1, location=(offset_x - 1.8, 2.2, 0.5))",
            "chair_l = bpy.context.active_object; chair_l.name = 'Armchair_Left.002'; chair_l.scale = (1.1, 1.1, 1.0); chair_l.rotation_euler = (0, 0, math.radians(35)); chair_l.data.materials.append(mat_red_velvet)",
            "",
            "bpy.ops.mesh.primitive_cube_add(size=1, location=(offset_x + 1.8, 2.2, 0.5))",
            "chair_r = bpy.context.active_object; chair_r.name = 'Armchair_Right.002'; chair_r.scale = (1.1, 1.1, 1.0); chair_r.rotation_euler = (0, 0, math.radians(-35)); chair_r.data.materials.append(mat_red_velvet)",
            "",
            "bpy.ops.mesh.primitive_cylinder_add(radius=0.7, depth=0.5, location=(offset_x, 2.2, 0.25))",
            "table = bpy.context.active_object; table.name = 'Coffee_Table.002'; table.data.materials.append(mat_wood_floor)",
            "",
            "# 5. Actors (Man in Dark Suit & Woman in Yellow Dress)",
            "# Man Actor (Left)",
            "bpy.ops.mesh.primitive_cylinder_add(radius=0.35, depth=0.7, location=(offset_x - 1.8, 2.2, 0.8))",
            "man_t = bpy.context.active_object; man_t.name = 'Actor_Man_Torso.002'; man_t.data.materials.append(mat_gear)",
            "bpy.ops.mesh.primitive_uv_sphere_add(radius=0.22, location=(offset_x - 1.8, 2.2, 1.35))",
            "man_h = bpy.context.active_object; man_h.name = 'Actor_Man_Head.002'; man_h.data.materials.append(mat_skin); bpy.ops.object.shade_smooth()",
            "",
            "# Woman Actor (Right in Yellow Dress)",
            "bpy.ops.mesh.primitive_cone_add(radius1=0.45, depth=0.8, location=(offset_x + 1.8, 2.2, 0.8))",
            "wom_t = bpy.context.active_object; wom_t.name = 'Actor_Woman_Torso.002'; wom_t.data.materials.append(mat_yellow_dress)",
            "bpy.ops.mesh.primitive_uv_sphere_add(radius=0.20, location=(offset_x + 1.8, 2.2, 1.35))",
            "wom_h = bpy.context.active_object; wom_h.name = 'Actor_Woman_Head.002'; wom_h.data.materials.append(mat_skin); bpy.ops.object.shade_smooth()",
            "",
            "# 6. Film Set Equipment (Camera Rig, Boom Mic, Lights, Sound Gear)",
            "# Cinema Camera on Tripod",
            "bpy.ops.mesh.primitive_cylinder_add(radius=0.08, depth=1.6, location=(offset_x, -2.5, 0.8))",
            "tripod = bpy.context.active_object; tripod.name = 'Camera_Tripod_Stand.002'; tripod.data.materials.append(mat_gear)",
            "bpy.ops.mesh.primitive_cube_add(size=1, location=(offset_x, -2.5, 1.6))",
            "cam_body = bpy.context.active_object; cam_body.name = 'Movie_Camera_Body.002'; cam_body.scale = (0.5, 0.8, 0.5); cam_body.data.materials.append(mat_gear)",
            "",
            "# Boom Pole & Furry Mic",
            "bpy.ops.mesh.primitive_cylinder_add(radius=0.03, depth=3.2, location=(offset_x - 1.0, 1.0, 2.8), rotation=(math.radians(20), math.radians(45), 0))",
            "boom_p = bpy.context.active_object; boom_p.name = 'Boom_Pole.002'; boom_p.data.materials.append(mat_gear)",
            "bpy.ops.mesh.primitive_cylinder_add(radius=0.10, depth=0.45, location=(offset_x, 2.0, 2.3))",
            "boom_m = bpy.context.active_object; boom_m.name = 'Boom_Microphone_Furry.002'; boom_m.data.materials.append(mat_gear)",
            "",
            "# Softboxes & Lighting Setup",
            "# Key Light (Left)",
            "bpy.ops.mesh.primitive_cube_add(size=1, location=(offset_x - 3.5, -1.0, 2.5), rotation=(math.radians(15), math.radians(-20), math.radians(-40)))",
            "sb_l = bpy.context.active_object; sb_l.name = 'Softbox_Light_Left.002'; sb_l.scale = (0.2, 1.2, 1.2); sb_l.data.materials.append(mat_gear)",
            "bpy.ops.object.light_add(type='SPOT', location=(offset_x - 3.5, -1.0, 2.5))",
            "spot_key = bpy.context.active_object; spot_key.name = 'Spotlight_Key.002'; spot_key.data.energy = 300.0; spot_key.data.color = (1.0, 0.96, 0.90)",
            "",
            "# Fill Light (Right)",
            "bpy.ops.mesh.primitive_cube_add(size=1, location=(offset_x + 3.5, -1.0, 2.5), rotation=(math.radians(15), math.radians(20), math.radians(40)))",
            "sb_r = bpy.context.active_object; sb_r.name = 'Softbox_Light_Right.002'; sb_r.scale = (0.2, 1.2, 1.2); sb_r.data.materials.append(mat_gear)",
            "bpy.ops.object.light_add(type='SPOT', location=(offset_x + 3.5, -1.0, 2.5))",
            "spot_fill = bpy.context.active_object; spot_fill.name = 'Spotlight_Fill.002'; spot_fill.data.energy = 160.0; spot_fill.data.color = (0.92, 0.95, 1.0)",
            "",
            "# 7. Extra Backstage Details (Director Chair & Production Gear Cases)",
            "bpy.ops.mesh.primitive_cube_add(size=1, location=(offset_x - 3.2, -3.0, 0.5))",
            "dir_chair = bpy.context.active_object; dir_chair.name = 'Director_Chair.002'; dir_chair.scale = (0.8, 0.8, 0.9); dir_chair.data.materials.append(mat_gear)",
            "bpy.ops.mesh.primitive_cube_add(size=1, location=(offset_x + 3.5, -3.2, 0.4))",
            "gear_case = bpy.context.active_object; gear_case.name = 'Production_Flight_Case.002'; gear_case.scale = (1.2, 0.8, 0.7); gear_case.data.materials.append(mat_gear)",
        ])
        explanation = "Constructed 3rd film set scene beside previous two (offset X=44) featuring fireplace, armchairs with actors, movie camera rig, boom mic, and studio lighting."

    else:
        # Generic abstract geometry builder tailored to prompt
        code_lines.extend([
            "# Procedural Geometric Composition",
            "mat = create_material('Composition_Mat', color=(0.85, 0.35, 0.15, 1.0), metallic=0.5, roughness=0.2)",
            "bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1.8, location=(offset_x, 0, 1.8))",
            "geom = bpy.context.active_object",
            "geom.name = 'Imperal_Geometry'",
            "geom.data.materials.append(mat)",
            "bpy.ops.object.shade_smooth()",
        ])
        explanation = f"Generated 3D geometry based on prompt: '{prompt}'."

    # Full studio lighting & camera for new scenes
    if target_mode == "new_scene" and not is_beside:
        code_lines.extend([
            "",
            "# Studio Lighting & Camera",
            "bpy.ops.object.light_add(type='SUN', location=(offset_x + 5, -5, 8))",
            "sun = bpy.context.active_object; sun.name = 'Sun_Key'; sun.data.energy = 3.5",
            "bpy.ops.object.camera_add(location=(offset_x + 6, -7, 4.5), rotation=(math.radians(65), 0, math.radians(40)))",
            "cam = bpy.context.active_object; cam.name = 'Main_Camera'",
            "bpy.context.scene.camera = cam",
        ])

    return "\n".join(code_lines), explanation

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

    elif any(w in prompt_lower for w in ["room", "set", "movie", "film", "fireplace", "комнат", "сцена", "площадк", "камин"]):
        # Dynamic procedural film set / room with adaptive props
        code_lines.extend([
            "# Procedural Film Set / Room Composition",
            "mat_wood = create_material('Wood_Floor_Mat', color=(0.25, 0.14, 0.08, 1.0), roughness=0.35)",
            "mat_wall = create_material('Interior_Wall_Mat', color=(0.18, 0.20, 0.24, 1.0), roughness=0.7)",
            "mat_accent = create_material('Accent_Red_Mat', color=(0.55, 0.08, 0.12, 1.0), roughness=0.6)",
            "",
            "# Floor & Back Wall",
            "bpy.ops.mesh.primitive_plane_add(size=10, location=(offset_x, 0, 0))",
            "floor = bpy.context.active_object; floor.name = 'Floor'; floor.data.materials.append(mat_wood)",
            "bpy.ops.mesh.primitive_cube_add(size=1, location=(offset_x, 4.5, 2.5))",
            "wall = bpy.context.active_object; wall.name = 'Back_Wall'; wall.scale = (10.0, 0.2, 5.0); wall.data.materials.append(mat_wall)",
            "",
            "# Centerpiece / Fireplace",
            "mat_stone = create_material('Stone_Mat', color=(0.82, 0.80, 0.76, 1.0), roughness=0.45)",
            "bpy.ops.mesh.primitive_cube_add(size=1, location=(offset_x, 4.2, 1.2))",
            "fp = bpy.context.active_object; fp.name = 'Center_Fireplace'; fp.scale = (3.0, 0.6, 2.4); fp.data.materials.append(mat_stone)",
            "bpy.ops.object.light_add(type='POINT', location=(offset_x, 4.0, 0.8))",
            "fire_light = bpy.context.active_object; fire_light.name = 'Fire_Glow'; fire_light.data.color = (1.0, 0.45, 0.1); fire_light.data.energy = 90.0",
            "",
            "# Seating & Furniture",
            "bpy.ops.mesh.primitive_cube_add(size=1, location=(offset_x - 1.6, 1.8, 0.5))",
            "c1 = bpy.context.active_object; c1.name = 'Armchair_Left'; c1.scale = (1.0, 1.0, 0.9); c1.rotation_euler = (0, 0, math.radians(30)); c1.data.materials.append(mat_accent)",
            "bpy.ops.mesh.primitive_cube_add(size=1, location=(offset_x + 1.6, 1.8, 0.5))",
            "c2 = bpy.context.active_object; c2.name = 'Armchair_Right'; c2.scale = (1.0, 1.0, 0.9); c2.rotation_euler = (0, 0, math.radians(-30)); c2.data.materials.append(mat_accent)",
            "bpy.ops.mesh.primitive_cylinder_add(radius=0.6, depth=0.45, location=(offset_x, 1.8, 0.22))",
            "tbl = bpy.context.active_object; tbl.name = 'Coffee_Table'; tbl.data.materials.append(mat_wood)",
            "",
            "# Production Gear (Camera & Key Light)",
            "mat_black = create_material('Gear_Black_Mat', color=(0.04, 0.04, 0.04, 1.0), roughness=0.3, metallic=0.8)",
            "bpy.ops.mesh.primitive_cylinder_add(radius=0.06, depth=1.5, location=(offset_x, -2.5, 0.75))",
            "tripod = bpy.context.active_object; tripod.name = 'Camera_Stand'; tripod.data.materials.append(mat_black)",
            "bpy.ops.object.light_add(type='SPOT', location=(offset_x - 3.0, -1.0, 2.6))",
            "key_light = bpy.context.active_object; key_light.name = 'Key_Spotlight'; key_light.data.energy = 250.0; key_light.data.color = (1.0, 0.95, 0.9)",
        ])
        explanation = "Created a procedural film set room composition with warm hearth, seating area, and studio lighting."

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

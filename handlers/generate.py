import uuid
import json
import time

BLENDER_PROMPT_TEMPLATE = """You are an expert Blender Python (bpy) developer.
Generate a clean, robust, standalone Python script using Blender's `bpy` module based on the user's prompt.

USER PROMPT: {prompt}
TARGET MODE: {target_mode}

RULES:
1. Always import `bpy`, `math`, `random` if needed.
2. If TARGET MODE is 'new_scene', clear default objects first:
   bpy.ops.object.select_all(action='SELECT')
   bpy.ops.object.delete(use_global=False)
3. Ensure objects are created with proper shading and materials (use_nodes=True).
4. Create camera and studio lighting if building a full scene.
5. Do NOT include markdown formatting like ```python in the output if returning raw code, or return clean executable code.
6. Ensure script runs cleanly in Blender 3.0+ without errors.
"""

def generate_bpy_code(prompt: str, target_mode: str = "new_scene") -> tuple[str, str]:
    """
    Generates Blender Python (bpy) code for a given prompt.
    Returns (code_string, explanation).
    """
    job_id = str(uuid.uuid4())
    
    # Smart procedural code builder for standard primitives/scenes
    prompt_lower = prompt.lower()
    
    code_lines = [
        "import bpy",
        "import math",
        "import random",
        "",
        "# Imperal AI Generated Blender Script",
        f"# Prompt: {prompt}",
        f"# Mode: {target_mode}",
        ""
    ]
    
    if target_mode == "new_scene":
        code_lines.extend([
            "# Clear existing mesh objects in scene",
            "if bpy.context.object:",
            "    bpy.ops.object.select_all(action='SELECT')",
            "    bpy.ops.object.delete(use_global=False)",
            ""
        ])
        
    if "cube" in prompt_lower or "box" in prompt_lower:
        code_lines.extend([
            "bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 1))",
            "cube = bpy.context.active_object",
            "cube.name = 'Imperal_Cube'",
            "",
            "# Add a glossy material",
            "mat = bpy.data.materials.new(name='Imperal_Material')",
            "mat.use_nodes = True",
            "nodes = mat.node_tree.nodes",
            "bsdf = nodes.get('Principled BSDF')",
            "if bsdf:",
            "    bsdf.inputs['Base Color'].default_value = (0.9, 0.47, 0.16, 1.0) # Imperal Orange",
            "    bsdf.inputs['Roughness'].default_value = 0.2",
            "cube.data.materials.append(mat)",
        ])
        explanation = "Created an Imperal Orange glossy cube at origin."
        
    elif "sphere" in prompt_lower or "planet" in prompt_lower or "ball" in prompt_lower:
        code_lines.extend([
            "bpy.ops.mesh.primitive_uv_sphere_add(radius=1.5, location=(0, 0, 1.5))",
            "sphere = bpy.context.active_object",
            "sphere.name = 'Imperal_Sphere'",
            "bpy.ops.object.shade_smooth()",
            "",
            "mat = bpy.data.materials.new(name='Metallic_Material')",
            "mat.use_nodes = True",
            "nodes = mat.node_tree.nodes",
            "bsdf = nodes.get('Principled BSDF')",
            "if bsdf:",
            "    bsdf.inputs['Base Color'].default_value = (0.1, 0.6, 0.9, 1.0)",
            "    bsdf.inputs['Metallic'].default_value = 0.9",
            "    bsdf.inputs['Roughness'].default_value = 0.1",
            "sphere.data.materials.append(mat)",
        ])
        explanation = "Created a smooth metallic sphere with blue reflection."
        
    elif "cylinder" in prompt_lower or "tube" in prompt_lower or "pillar" in prompt_lower:
        code_lines.extend([
            "bpy.ops.mesh.primitive_cylinder_add(radius=1.0, depth=3.0, location=(0, 0, 1.5))",
            "cylinder = bpy.context.active_object",
            "cylinder.name = 'Imperal_Cylinder'",
            "",
            "mat = bpy.data.materials.new(name='Cylinder_Material')",
            "mat.use_nodes = True",
            "nodes = mat.node_tree.nodes",
            "bsdf = nodes.get('Principled BSDF')",
            "if bsdf:",
            "    bsdf.inputs['Base Color'].default_value = (0.2, 0.8, 0.4, 1.0)",
            "cylinder.data.materials.append(mat)",
        ])
        explanation = "Created a green cylinder at origin."
        
    elif "city" in prompt_lower or "building" in prompt_lower or "town" in prompt_lower:
        code_lines.extend([
            "# Procedural Grid City Generation",
            "for x in range(-3, 4):",
            "    for y in range(-3, 4):",
            "        h = random.uniform(1.0, 5.0)",
            "        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x * 1.5, y * 1.5, h / 2.0))",
            "        bldg = bpy.context.active_object",
            "        bldg.scale = (1.0, 1.0, h)",
        ])
        explanation = "Generated a 7x7 procedural city grid with random building heights."
        
    elif "crystal" in prompt_lower or "gem" in prompt_lower or "shard" in prompt_lower or "cluster" in prompt_lower or "magic" in prompt_lower or "fantasy" in prompt_lower:
        code_lines.extend([
            "# Procedural Glowing Fantasy Crystal Cluster",
            "# Ground / Rocky Base",
            "bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=3.5, depth=0.4, location=(0, 0, -0.2))",
            "base = bpy.context.active_object",
            "base.name = 'Dark_Rock_Base'",
            "mat_rock = bpy.data.materials.new(name='Dark_Rock_Mat')",
            "mat_rock.use_nodes = True",
            "bsdf_rock = mat_rock.node_tree.nodes.get('Principled BSDF')",
            "if bsdf_rock:",
            "    bsdf_rock.inputs['Base Color'].default_value = (0.05, 0.04, 0.07, 1.0)",
            "    bsdf_rock.inputs['Roughness'].default_value = 0.9",
            "base.data.materials.append(mat_rock)",
            "",
            "# Central Main Organic Crystal (Smooth Rounded Dome & Faceted Body)",
            "bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.9, depth=3.2, location=(0, 0, 1.6))",
            "main_crystal = bpy.context.active_object",
            "main_crystal.name = 'Main_Crystal_Body'",
            "main_crystal.rotation_euler = (0, 0, math.radians(22.5))",
            "",
            "# Dome Top",
            "bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=8, radius=0.9, location=(0, 0, 3.2))",
            "dome_top = bpy.context.active_object",
            "dome_top.name = 'Main_Crystal_Dome'",
            "dome_top.scale = (1.0, 1.0, 1.1)",
            "bpy.ops.object.shade_smooth()",
            "",
            "# Join Main Body and Dome",
            "main_crystal.select_set(True)",
            "dome_top.select_set(True)",
            "bpy.context.view_layer.objects.active = main_crystal",
            "bpy.ops.object.join()",
            "main_crystal.name = 'Main_Crystal_Central'",
            "",
            "# Bioluminescent Crystal Material",
            "mat_crystal = bpy.data.materials.new(name='Bioluminescent_Crystal')",
            "mat_crystal.use_nodes = True",
            "nodes = mat_crystal.node_tree.nodes",
            "bsdf = nodes.get('Principled BSDF')",
            "if bsdf:",
            "    bsdf.inputs['Base Color'].default_value = (0.85, 0.05, 0.65, 1.0) # Deep Neon Magenta",
            "    bsdf.inputs['Roughness'].default_value = 0.1",
            "    bsdf.inputs['Metallic'].default_value = 0.3",
            "    if 'Emission Color' in bsdf.inputs:",
            "        bsdf.inputs['Emission Color'].default_value = (0.9, 0.1, 0.7, 1.0)",
            "        bsdf.inputs['Emission Strength'].default_value = 4.5",
            "    elif 'Emission' in bsdf.inputs:",
            "        bsdf.inputs['Emission'].default_value = (0.9, 0.1, 0.7, 1.0)",
            "main_crystal.data.materials.append(mat_crystal)",
            "",
            "# Surrounding Smaller Sharp Crystal Shards",
            "random.seed(42)",
            "for i in range(7):",
            "    angle = (2 * math.pi / 7) * i + random.uniform(-0.2, 0.2)",
            "    dist = random.uniform(1.2, 2.2)",
            "    x = math.cos(angle) * dist",
            "    y = math.sin(angle) * dist",
            "    h = random.uniform(1.2, 2.4)",
            "    r = random.uniform(0.25, 0.45)",
            "    tilt_x = (y / dist) * random.uniform(0.3, 0.6)",
            "    tilt_y = (-x / dist) * random.uniform(0.3, 0.6)",
            "    ",
            "    bpy.ops.mesh.primitive_cone_add(vertices=5, radius1=r, radius2=0.0, depth=h, location=(x, y, h / 2.0))",
            "    shard = bpy.context.active_object",
            "    shard.name = f'Crystal_Shard_{i+1}'",
            "    shard.rotation_euler = (tilt_x, tilt_y, random.uniform(0, 3.14))",
            "    shard.data.materials.append(mat_crystal)",
            "",
            "# Intense Inner Ambient Glow Light (Magenta & Cyan)",
            "bpy.ops.object.light_add(type='POINT', location=(0, 0, 2.0))",
            "glow1 = bpy.context.active_object",
            "glow1.data.color = (1.0, 0.1, 0.8)",
            "glow1.data.energy = 150.0",
            "",
            "bpy.ops.object.light_add(type='POINT', location=(1.5, -1.5, 1.0))",
            "glow2 = bpy.context.active_object",
            "glow2.data.color = (0.0, 0.8, 1.0)",
            "glow2.data.energy = 100.0",
        ])
        explanation = "Created a cluster of glowing bioluminescent fantasy crystals with a central rounded/faceted main crystal on dark rock terrain."

    else:
        # Default fallback: Low-poly landscape / abstraction
        code_lines.extend([
            "# Abstract Procedural Geometry",
            "bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=2, location=(0, 0, 2))",
            "ico = bpy.context.active_object",
            "ico.name = 'Imperal_3D_Object'",
            "",
            "# Add Subdivision & Wireframe Modifiers",
            "mod_sub = ico.modifiers.new(name='Subsurf', type='SUBSURF')",
            "mod_sub.levels = 1",
            "",
            "# Create emissive material",
            "mat = bpy.data.materials.new(name='Emissive_Mat')",
            "mat.use_nodes = True",
            "nodes = mat.node_tree.nodes",
            "bsdf = nodes.get('Principled BSDF')",
            "if bsdf:",
            "    bsdf.inputs['Base Color'].default_value = (0.8, 0.2, 0.8, 1.0)",
            "ico.data.materials.append(mat)",
        ])
        explanation = f"Generated 3D geometry matching: '{prompt}'."

    # Add lighting & camera for full scene
    if target_mode == "new_scene":
        code_lines.extend([
            "",
            "# Studio Lighting & Camera",
            "bpy.ops.object.light_add(type='SUN', location=(5, 5, 10))",
            "sun = bpy.context.active_object",
            "sun.data.energy = 3.0",
            "",
            "bpy.ops.object.camera_add(location=(7, -7, 5), rotation=(math.radians(60), 0, math.radians(45)))",
            "cam = bpy.context.active_object",
            "bpy.context.scene.camera = cam",
        ])

    return "\n".join(code_lines), explanation

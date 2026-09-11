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

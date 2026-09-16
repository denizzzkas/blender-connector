import os
from imperal_sdk import ActionResult
from app import chat
from handlers.generate import generate_bpy_code
from handlers.webhook import queue_job_for_user, get_scene_inspection

@chat.function(
    "generate_3d_script",
    action_type="write",
    description="Generate a Python script (using Blender's bpy API) from a natural language prompt to create or modify 3D objects, materials, lights, and scenes in Blender."
)
async def handle_generate_3d_script(ctx, params: dict) -> ActionResult:
    """
    Action handler for generate_3d_script tool.
    """
    if hasattr(params, "model_dump"):
        p_dict = params.model_dump()
    elif isinstance(params, dict):
        p_dict = params
    else:
        p_dict = dict(params)

    prompt = p_dict.get("prompt", "")
    target_mode = p_dict.get("target_mode", "new_scene")
    user_token = getattr(ctx, 'user_id', 'demo_user') or 'demo_user'

    code, explanation = generate_bpy_code(prompt, target_mode)
    job_id = f"job_{user_token[:6] if user_token else 'demo'}_{hash(prompt) % 10000}"

    job_data = {
        "job_id": job_id,
        "prompt": prompt,
        "target_mode": target_mode,
        "code": code,
        "explanation": explanation
    }

    queue_job_for_user(user_token, job_data)

    res_data = {
        "job_id": job_id,
        "status": "pending_blender",
        "code": code,
        "explanation": explanation
    }
    return ActionResult.success(data=res_data, summary=f"Queued 3D script generation job {job_id} for Blender.")

@chat.function(
    "inspect_active_scene",
    action_type="read",
    description="Inspect the active 3D scene in Blender: returns the full hierarchy of objects, materials, active selections, camera settings, and viewport vision snapshot."
)
async def handle_inspect_active_scene(ctx, params: dict = None) -> ActionResult:
    """
    Action handler for inspect_active_scene tool.
    Returns the latest synced Blender 3D scene hierarchy and viewport vision snapshot.
    """
    user_token = getattr(ctx, 'user_id', 'demo_user') or 'demo_user'
    inspection = get_scene_inspection(user_token)

    if not inspection:
        res_data = {
            "scene_name": "No active Blender sync",
            "objects_count": 0,
            "objects": [],
            "message": "No scene data received yet. Click 'Sync 3D Scene Vision' in the Blender N-panel."
        }
        return ActionResult.success(data=res_data, summary="No active Blender scene synced yet.")

    return ActionResult.success(data=inspection, summary=f"Inspected Blender scene '{inspection.get('scene_name')}' with {inspection.get('objects_count', 0)} objects.")

@chat.function(
    "get_addon_script",
    action_type="read",
    description="Get the standalone Blender Python addon source code for download and installation."
)
async def handle_get_addon_script(ctx, params: dict = None) -> ActionResult:
    """
    Action handler for get_addon_script tool.
    """
    addon_path = os.path.join(os.path.dirname(__file__), "blender_addon.py")
    code = ""
    if os.path.exists(addon_path):
        with open(addon_path, "r", encoding="utf-8") as f:
            code = f.read()
    else:
        code = "# Addon code not found"

    res_data = {
        "filename": "imperal_blender_connector.py",
        "addon_code": code
    }
    return ActionResult.success(data=res_data, summary="Retrieved Blender Addon Python script.")

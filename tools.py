import os
from handlers.generate import generate_bpy_code
from handlers.webhook import queue_job_for_user, get_scene_inspection

async def handle_generate_3d_script(ctx, params: dict) -> dict:
    """
    Action handler for generate_3d_script tool.
    """
    prompt = params.get("prompt", "")
    target_mode = params.get("target_mode", "new_scene")
    user_token = ctx.user_id if hasattr(ctx, 'user_id') and ctx.user_id else "demo_user"

    code, explanation = generate_bpy_code(prompt, target_mode)
    job_id = f"job_{ctx.user_id[:6] if hasattr(ctx, 'user_id') and ctx.user_id else 'demo'}_{hash(prompt) % 10000}"

    job_data = {
        "job_id": job_id,
        "prompt": prompt,
        "target_mode": target_mode,
        "code": code,
        "explanation": explanation
    }

    queue_job_for_user(user_token, job_data)

    return {
        "job_id": job_id,
        "status": "pending_blender",
        "code": code,
        "explanation": explanation
    }

async def handle_inspect_active_scene(ctx, params: dict) -> dict:
    """
    Action handler for inspect_active_scene tool.
    Returns the latest synced Blender 3D scene hierarchy and viewport vision snapshot.
    """
    user_token = ctx.user_id if hasattr(ctx, 'user_id') and ctx.user_id else "demo_user"
    inspection = get_scene_inspection(user_token)

    if not inspection:
        return {
            "scene_name": "No active Blender sync",
            "objects_count": 0,
            "objects": [],
            "message": "No scene data received yet. Click 'Sync 3D Scene Vision' in the Blender N-panel."
        }

    return inspection

async def handle_get_addon_script(ctx, params: dict) -> dict:
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

    return {
        "filename": "imperal_blender_connector.py",
        "addon_code": code
    }

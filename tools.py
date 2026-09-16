import os
from imperal_sdk import ActionResult
from app import chat
from handlers.generate import generate_bpy_code
from handlers.webhook import queue_job_for_user, get_scene_inspection
from models import (
    Generate3DParams,
    Generate3DResult,
    InspectSceneParams,
    InspectSceneResult,
    GetAddonParams,
    GetAddonResult,
)


@chat.function(
    "generate_3d_script",
    action_type="write",
    data_model=Generate3DResult,
    description="Generate a Python script (using Blender's bpy API) from a natural language prompt to create or modify 3D objects, materials, lights, and scenes in Blender.",
)
async def handle_generate_3d_script(ctx, params: Generate3DParams) -> ActionResult:
    """Action handler for generate_3d_script tool."""
    prompt = params.prompt
    target_mode = params.target_mode
    user_token = getattr(ctx, "user_id", "demo_user") or "demo_user"

    code, explanation = generate_bpy_code(prompt, target_mode)
    job_id = f"job_{user_token[:6] if user_token else 'demo'}_{hash(prompt) % 10000}"

    job_data = {
        "job_id": job_id,
        "prompt": prompt,
        "target_mode": target_mode,
        "code": code,
        "explanation": explanation,
    }

    queue_job_for_user(user_token, job_data)

    res = Generate3DResult(
        job_id=job_id,
        status="pending_blender",
        code=code,
        explanation=explanation,
    )
    return ActionResult.success(
        data=res, summary=f"Queued 3D script generation job {job_id} for Blender."
    )


@chat.function(
    "inspect_active_scene",
    action_type="read",
    data_model=InspectSceneResult,
    description="Inspect the active 3D scene in Blender: returns the full hierarchy of objects, materials, active selections, camera settings, and viewport vision snapshot.",
)
async def handle_inspect_active_scene(ctx, params: InspectSceneParams = InspectSceneParams()) -> ActionResult:
    """Action handler for inspect_active_scene tool."""
    user_token = getattr(ctx, "user_id", "demo_user") or "demo_user"
    inspection = get_scene_inspection(user_token)

    if not inspection:
        res = InspectSceneResult(
            scene_name="No active Blender sync",
            objects_count=0,
            objects=[],
            message="No scene data received yet. Click 'Sync 3D Scene Vision' in the Blender N-panel.",
        )
        return ActionResult.success(data=res, summary="No active Blender scene sync found.")

    res = InspectSceneResult(
        scene_name=inspection.get("scene_name", "Scene"),
        objects_count=inspection.get("objects_count", 0),
        active_object=inspection.get("active_object"),
        selected_objects=inspection.get("selected_objects", []),
        objects=inspection.get("objects", []),
        viewport_snapshot=inspection.get("viewport_snapshot"),
    )
    return ActionResult.success(data=res, summary=f"Inspected Blender scene '{res.scene_name}' with {res.objects_count} objects.")


@chat.function(
    "get_addon_script",
    action_type="read",
    data_model=GetAddonResult,
    description="Get the standalone Blender Python addon source code for download and installation.",
)
async def handle_get_addon_script(ctx, params: GetAddonParams = GetAddonParams()) -> ActionResult:
    """Action handler for get_addon_script tool."""
    script_path = os.path.join(os.path.dirname(__file__), "blender_addon.py")
    if not os.path.exists(script_path):
        return ActionResult.error("blender_addon.py not found on disk.")

    with open(script_path, "r", encoding="utf-8") as f:
        addon_code = f.read()

    res = GetAddonResult(
        filename="imperal_blender_connector.py",
        addon_code=addon_code,
        version="1.1.0",
    )
    return ActionResult.success(data=res, summary="Retrieved Blender connector addon source code.")

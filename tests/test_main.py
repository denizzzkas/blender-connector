import pytest
import os
import json
from handlers.generate import generate_bpy_code
from handlers.webhook import queue_job_for_user, get_job_status, store_scene_inspection, get_scene_inspection, _JOB_QUEUE, _JOB_STATUSES
from tools import handle_generate_3d_script, handle_inspect_active_scene, handle_get_addon_script

class DummyContext:
    def __init__(self, user_id="test_user_123"):
        self.user_id = user_id

@pytest.mark.asyncio
async def test_generate_bpy_code():
    code, explanation = generate_bpy_code("create a red sphere", target_mode="new_scene")
    assert "primitive_uv_sphere_add" in code
    assert "import bpy" in code
    assert len(explanation) > 0

@pytest.mark.asyncio
async def test_generate_action():
    ctx = DummyContext()
    params = {"prompt": "neon metallic cube", "target_mode": "new_scene"}
    res = await handle_generate_3d_script(ctx, params)
    assert "job_id" in res
    assert res["status"] == "pending_blender"
    assert "primitive_cube_add" in res["code"]

    # Verify queued job
    status = get_job_status(res["job_id"])
    assert status["status"] == "pending_blender"

@pytest.mark.asyncio
async def test_inspect_active_scene():
    ctx = DummyContext()
    dummy_scene_data = {
        "scene_name": "Scene_Test",
        "objects_count": 2,
        "active_object": "Imperal_Cube",
        "objects": [{"name": "Imperal_Cube", "type": "MESH"}],
        "viewport_snapshot": "base64_sample_jpeg"
    }
    store_scene_inspection("test_user_123", dummy_scene_data)
    
    res = await handle_inspect_active_scene(ctx, {})
    assert res["scene_name"] == "Scene_Test"
    assert res["objects_count"] == 2
    assert res["viewport_snapshot"] == "base64_sample_jpeg"

@pytest.mark.asyncio
async def test_get_addon_script():
    ctx = DummyContext()
    res = await handle_get_addon_script(ctx, {})
    assert res["filename"] == "imperal_blender_connector.py"
    assert "bl_info" in res["addon_code"]
    assert "get_scene_inspection_data" in res["addon_code"]

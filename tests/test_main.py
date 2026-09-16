import pytest
import os
import json
import main
from handlers.generate import generate_bpy_code
from handlers.webhook import (
    queue_job_for_user,
    get_job_status,
    store_scene_inspection,
    get_scene_inspection,
    _JOB_QUEUE,
    _JOB_STATUSES
)
from tools import handle_generate_3d_script, handle_inspect_active_scene, handle_get_addon_script
from models import Generate3DParams, InspectSceneParams, GetAddonParams
from panels import render_status_panel, render_studio_panel
from app import ext

class DummyContext:
    def __init__(self, user_id="test_user_123"):
        self.user_id = user_id

class DummyRequest:
    def __init__(self, query_params=None):
        self.query_params = query_params or {}

@pytest.mark.asyncio
async def test_generate_bpy_code_primitives():
    code_cube, exp_cube = generate_bpy_code("create a blue cube", target_mode="new_scene")
    assert "primitive_cube_add" in code_cube
    assert "new_scene" in code_cube
    assert len(exp_cube) > 0

    code_sphere, exp_sphere = generate_bpy_code("make a sphere", target_mode="modify_active")
    assert "primitive_uv_sphere_add" in code_sphere
    assert "modify_active" in code_sphere

    code_cylinder, _ = generate_bpy_code("cylinder light")
    assert "primitive_cylinder_add" in code_cylinder

    code_generic, _ = generate_bpy_code("a futuristic flying car with neon lights")
    assert "import bpy" in code_generic

@pytest.mark.asyncio
async def test_generate_action():
    ctx = DummyContext("usr_abc123")
    params = Generate3DParams(prompt="neon metallic cube", target_mode="new_scene")
    res = await handle_generate_3d_script(ctx, params)
    data = res.data
    assert data.job_id is not None
    assert data.status == "pending_blender"
    assert "primitive_cube_add" in data.code

    status = get_job_status(data.job_id)
    assert status["status"] == "pending_blender"

@pytest.mark.asyncio
async def test_inspect_active_scene():
    ctx = DummyContext("usr_inspect_999")
    
    # Before sync
    empty_res = await handle_inspect_active_scene(ctx, InspectSceneParams())
    empty_data = empty_res.data
    assert empty_data.objects_count == 0

    # After sync
    dummy_scene_data = {
        "scene_name": "Scene_Test",
        "objects_count": 2,
        "active_object": "Cube",
        "selected_objects": ["Cube"],
        "viewport_snapshot": "base64_sample_jpeg"
    }
    store_scene_inspection("usr_inspect_999", dummy_scene_data)
    
    res = await handle_inspect_active_scene(ctx, InspectSceneParams())
    data = res.data
    assert data.scene_name == "Scene_Test"
    assert data.objects_count == 2
    assert data.viewport_snapshot == "base64_sample_jpeg"

@pytest.mark.asyncio
async def test_get_addon_script():
    ctx = DummyContext()
    res = await handle_get_addon_script(ctx, GetAddonParams())
    data = res.data
    assert data.filename == "imperal_blender_connector.py"
    assert "bl_info" in data.addon_code
    assert "get_scene_inspection_data" in data.addon_code

@pytest.mark.asyncio
async def test_webhook_endpoints():
    webhook_def = ext._webhooks.get("/webhook")
    assert webhook_def is not None
    webhook_fn = webhook_def.func

    ctx = DummyContext()

    # Missing token
    req_no_token = DummyRequest({"action": "poll"})
    res_err = await webhook_fn(ctx, req_no_token)
    assert res_err["status_code"] == 400

    # Poll empty queue
    req_poll_empty = DummyRequest({"action": "poll", "token": "tok_123"})
    res_empty = await webhook_fn(ctx, req_poll_empty)
    assert res_empty["status_code"] == 200
    body_empty = json.loads(res_empty["body"])
    assert body_empty["has_job"] is False

    # Poll with job in queue
    queue_job_for_user("tok_123", {"job_id": "job_001", "prompt": "test cube"})
    req_poll_job = DummyRequest({"action": "poll", "token": "tok_123"})
    res_job = await webhook_fn(ctx, req_poll_job)
    assert res_job["status_code"] == 200
    body_job = json.loads(res_job["body"])
    assert body_job["has_job"] is True
    assert body_job["job"]["job_id"] == "job_001"

    # Sync inspection webhook
    req_sync = DummyRequest({
        "action": "sync_inspection",
        "token": "tok_123",
        "data": json.dumps({"scene_name": "SyncedScene", "objects_count": 5})
    })
    res_sync = await webhook_fn(ctx, req_sync)
    assert res_sync["status_code"] == 200

    inspection = get_scene_inspection("tok_123")
    assert inspection["scene_name"] == "SyncedScene"
    assert inspection["objects_count"] == 5

    # Report execution result webhook
    req_result = DummyRequest({
        "action": "result",
        "token": "tok_123",
        "job_id": "job_001",
        "status": "completed"
    })
    res_res = await webhook_fn(ctx, req_result)
    assert res_res["status_code"] == 200

    job_st = get_job_status("job_001")
    assert job_st["status"] == "completed"

@pytest.mark.asyncio
async def test_panels_rendering():
    ctx = DummyContext("test_user_123")
    
    status_panel_res = await render_status_panel(ctx)
    assert status_panel_res["title"] == "Blender Connector"
    assert len(status_panel_res["components"]) >= 3

    studio_panel_res = await render_studio_panel(ctx)
    assert studio_panel_res["title"] == "Blender 3D AI Studio"
    assert len(studio_panel_res["components"]) >= 2

def test_manifest_validation():
    assert main.ext is not None

    manifest_path = os.path.join(os.path.dirname(__file__), "..", "imperal.json")
    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["app_id"] == "blender-connector"
    assert data["version"] == "1.1.0"
    assert len(data["tools"]) == 3
    tool_names = [t["name"] for t in data["tools"]]
    assert "generate_3d_script" in tool_names
    assert "inspect_active_scene" in tool_names
    assert "get_addon_script" in tool_names

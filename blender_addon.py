bl_info = {
    "name": "Imperal Blender Connector",
    "author": "Imperal Cloud",
    "version": (1, 2, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > Imperal",
    "description": "Connects Blender to Imperal Cloud to execute AI 3D Python scripts & sync scene vision.",
    "category": "3D View",
}

import sys, os, io, json, base64, tempfile, threading, urllib.request, urllib.error, urllib.parse, importlib

bpy = sys.modules.get("bpy") or (importlib.import_module("bpy") if importlib.util.find_spec("bpy") else None)

class _Tee(io.TextIOBase):
    def __init__(self, orig):
        self._buf, self._orig = io.StringIO(), orig
    def write(self, s):
        self._orig.write(s)
        return self._buf.write(s)
    def flush(self):
        self._orig.flush()
        self._buf.flush()
    def getvalue(self):
        return self._buf.getvalue()

class CaptureOutput:
    def __enter__(self):
        self._orig_out, self._orig_err = sys.stdout, sys.stderr
        self._tee_out, self._tee_err = _Tee(sys.stdout), _Tee(sys.stderr)
        sys.stdout, sys.stderr = self._tee_out, self._tee_err
        return self
    def __exit__(self, et, ev, tb):
        sys.stdout, sys.stderr = self._orig_out, self._orig_err
    @property
    def stdout(self): return self._tee_out.getvalue()
    @property
    def stderr(self): return self._tee_err.getvalue()

def find_view3d():
    if not bpy: return (None, None, None)
    best, best_size = (None, None, None), -1
    for win in bpy.context.window_manager.windows:
        if not win.screen: continue
        for area in win.screen.areas:
            if area.type != "VIEW_3D": continue
            reg = next((r for r in area.regions if r.type == "WINDOW"), None)
            if reg and (area.width * area.height > best_size):
                best_size = area.width * area.height
                best = (win, area, reg)
    return best

def safe_object_mode():
    if bpy and hasattr(bpy.context, "mode") and bpy.context.mode != 'OBJECT':
        try: bpy.ops.object.mode_set(mode='OBJECT')
        except Exception: pass

def get_scene_inspection_data(include_viewport=True):
    if not bpy: return {}
    scene = bpy.context.scene
    active_obj = bpy.context.active_object
    objects_data = []

    for obj in scene.objects:
        mats = [s.material.name for s in obj.material_slots if s.material]
        info = {
            "name": obj.name, "type": obj.type,
            "location": [round(v, 3) for v in obj.location],
            "rotation": [round(v, 3) for v in obj.rotation_euler],
            "scale": [round(v, 3) for v in obj.scale],
            "is_selected": obj.select_get(), "is_active": (obj == active_obj),
            "materials": mats, "visible": obj.visible_get()
        }
        if obj.type == 'MESH' and obj.data:
            info["vertices_count"], info["polygons_count"] = len(obj.data.vertices), len(obj.data.polygons)
        elif obj.type == 'LIGHT' and obj.data:
            info["light_type"], info["energy"] = obj.data.type, obj.data.energy
        elif obj.type == 'CAMERA' and obj.data:
            info["focal_length"] = obj.data.lens
        objects_data.append(info)

    inspection = {
        "scene_name": scene.name, "objects_count": len(objects_data),
        "active_object": active_obj.name if active_obj else None,
        "selected_objects": [o.name for o in scene.objects if o.select_get()],
        "objects": objects_data, "viewport_snapshot": None
    }

    if include_viewport:
        try:
            snap_path = os.path.join(tempfile.gettempdir(), "imperal_viewport_preview.jpg")
            rd = scene.render
            orig_fp, orig_fmt, orig_pct, orig_q = rd.filepath, rd.image_settings.file_format, rd.resolution_percentage, rd.image_settings.quality
            rd.filepath = snap_path
            rd.image_settings.file_format, rd.image_settings.quality, rd.resolution_percentage = 'JPEG', 65, 30
            
            win, area, reg = find_view3d()
            if area and reg:
                override = {"window": win, "screen": win.screen, "area": area, "region": reg, "scene": scene}
                with bpy.context.temp_override(**override) if hasattr(bpy.context, "temp_override") else contextlib.nullcontext():
                    bpy.ops.render.opengl(write_still=True)
            else:
                bpy.ops.render.opengl(write_still=True)

            rd.filepath, rd.image_settings.file_format, rd.resolution_percentage, rd.image_settings.quality = orig_fp, orig_fmt, orig_pct, orig_q
            if os.path.exists(snap_path):
                with open(snap_path, "rb") as f:
                    inspection["viewport_snapshot"] = base64.b64encode(f.read()).decode('utf-8')
        except Exception as e:
            inspection["viewport_error"] = str(e)

    return inspection

class ImperalConnectorProperties(bpy.types.PropertyGroup if bpy else object):
    server_url: bpy.props.StringProperty(
        name="Server URL", description="Imperal Cloud Webhook URL", default="https://panel.imperal.io/v1/ext/blender-connector/webhook/"
    ) if bpy else ""
    user_token: bpy.props.StringProperty(
        name="User Token", description="Your Imperal Cloud User Token or ID", default="", subtype='PASSWORD'
    ) if bpy else ""
    auto_poll: bpy.props.BoolProperty(
        name="Auto-Poll & Run (Live)", description="Automatically fetch and execute AI 3D scripts", default=True
    ) if bpy else True
    include_viewport: bpy.props.BoolProperty(
        name="Send Viewport Screenshot", description="Attach 3D viewport preview image when syncing scene", default=True
    ) if bpy else True
    last_status: bpy.props.StringProperty(name="Status", default="Idle") if bpy else "Idle"

def _send_report_async(server_url, token, job_id, status, error="", output=""):
    def _worker():
        try:
            url = f"{server_url}?action=report&token={token}&job_id={job_id}&status={status}"
            payload = json.dumps({"error": error, "output": output}).encode('utf-8')
            req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json', 'User-Agent': 'ImperalBlenderAddon/1.2'})
            urllib.request.urlopen(req, timeout=10)
        except Exception: pass
    threading.Thread(target=_worker, daemon=True).start()

class IMPERAL_OT_check_queue(bpy.types.Operator if bpy else object):
    bl_idname = "imperal.check_queue"
    bl_label = "Check & Run Jobs"
    bl_description = "Fetch pending AI scripts from Imperal Cloud and execute in Blender"
    silent: bpy.props.BoolProperty(default=False) if bpy else False

    def execute(self, context):
        props = context.scene.imperal_connector
        server_url = props.server_url.strip()
        if not server_url.endswith("/"): server_url += "/"
        user_token = props.user_token.strip()
        if not user_token:
            if not self.silent: self.report({'ERROR'}, "Please enter your Imperal User Token in the N-panel")
            return {'CANCELLED'}

        scene_info = get_scene_inspection_data(include_viewport=False)
        payload = json.dumps({"scene_inspection": scene_info}).encode('utf-8')
        url = f"{server_url}?action=poll&token={user_token}"
        try:
            req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json', 'User-Agent': 'ImperalBlenderAddon/1.2'})
            with urllib.request.urlopen(req, timeout=8) as response:
                data = json.loads(response.read().decode('utf-8'))

            if data.get("has_job"):
                job = data["job"]
                job_id, code = job.get("job_id", ""), job.get("code", "")
                props.last_status = f"Executing job {job_id[:8]}..."
                safe_object_mode()
                
                captured_out, captured_err = "", ""
                exec_globals = {"bpy": bpy, "math": importlib.import_module("math"), "random": importlib.import_module("random"), "__name__": "__main__"}
                try:
                    with CaptureOutput() as cap:
                        compiled_code = compile(code, f"<imperal_job_{job_id[:6]}>", "exec")
                        eval(compiled_code, exec_globals)
                    captured_out = cap.stdout
                    props.last_status = f"Job {job_id[:8]} executed successfully!"
                    if not self.silent: self.report({'INFO'}, f"Imperal 3D script executed: {job_id[:8]}")
                    _send_report_async(server_url, user_token, job_id, "success", output=captured_out)
                    if hasattr(bpy.ops.imperal, "send_inspection"):
                        bpy.ops.imperal.send_inspection(silent=True)
                except Exception as e:
                    captured_err = f"{str(e)}\n{cap.stderr if 'cap' in locals() else ''}"
                    props.last_status = f"Error in job {job_id[:8]}: {str(e)[:40]}"
                    if not self.silent: self.report({'ERROR'}, f"Script error: {str(e)}")
                    _send_report_async(server_url, user_token, job_id, "error", error=captured_err, output=captured_out)
            else:
                props.last_status = "Connected (No pending jobs)"
                if not self.silent: self.report({'INFO'}, "No pending jobs.")
        except Exception as e:
            props.last_status = f"Connection error: {str(e)[:40]}"
            if not self.silent: self.report({'WARNING'}, f"Failed to connect to Imperal: {str(e)}")

        return {'FINISHED'}

class IMPERAL_OT_send_inspection(bpy.types.Operator if bpy else object):
    bl_idname = "imperal.send_inspection"
    bl_label = "Inspect & Vision Sync"
    bl_description = "Send full 3D scene structure and viewport screenshot to Imperal AI"
    silent: bpy.props.BoolProperty(default=False) if bpy else False

    def execute(self, context):
        props = context.scene.imperal_connector
        server_url = props.server_url.strip()
        if not server_url.endswith("/"): server_url += "/"
        user_token = props.user_token.strip()
        if not user_token:
            if not self.silent: self.report({'ERROR'}, "Please enter your Imperal User Token")
            return {'CANCELLED'}

        props.last_status = "Capturing scene & viewport..."
        inspection_data = get_scene_inspection_data(include_viewport=props.include_viewport)
        
        def _sync_worker():
            try:
                payload = json.dumps(inspection_data).encode('utf-8')
                url = f"{server_url}?action=sync_inspection&token={user_token}"
                req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json', 'User-Agent': 'ImperalBlenderAddon/1.2'})
                with urllib.request.urlopen(req, timeout=20) as resp:
                    res = json.loads(resp.read().decode('utf-8'))
                    props.last_status = "Scene & Vision synced!" if res.get("ok") else "Sync error"
            except Exception as e:
                props.last_status = f"Sync error: {str(e)[:40]}"

        threading.Thread(target=_sync_worker, daemon=True).start()
        if not self.silent: self.report({'INFO'}, "Scene structure & 3D vision sent to Webbee!")
        return {'FINISHED'}

def imperal_auto_poll_timer():
    if bpy is None or not hasattr(bpy, "context") or not hasattr(bpy.context, "scene"):
        return 3.0
    try:
        scene = bpy.context.scene
        if scene and hasattr(scene, "imperal_connector"):
            props = scene.imperal_connector
            if getattr(props, "auto_poll", False) and getattr(props, "user_token", ""):
                bpy.ops.imperal.check_queue(silent=True)
    except Exception: pass
    return 3.0

class IMPERAL_PT_panel(bpy.types.Panel if bpy else object):
    bl_label = "Imperal 3D AI"
    bl_idname = "IMPERAL_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Imperal'

    def draw(self, context):
        layout = self.layout
        props = context.scene.imperal_connector

        box = layout.box()
        box.label(text="Imperal Connection Settings", icon='WORLD')
        box.prop(props, "user_token")
        box.prop(props, "server_url")
        box.prop(props, "auto_poll")

        layout.separator()
        layout.operator("imperal.check_queue", icon='PLAY')
        
        box_vision = layout.box()
        box_vision.label(text="3D Scene Vision & Inspection", icon='RESTRICT_VIEW_OFF')
        box_vision.prop(props, "include_viewport")
        box_vision.operator("imperal.send_inspection", icon='VIEWZOOM')

        box_status = layout.box()
        box_status.label(text=f"Status: {props.last_status}", icon='INFO')

classes = (ImperalConnectorProperties, IMPERAL_OT_check_queue, IMPERAL_OT_send_inspection, IMPERAL_PT_panel)

def register():
    if not bpy: return
    for cls in classes: bpy.utils.register_class(cls)
    bpy.types.Scene.imperal_connector = bpy.props.PointerProperty(type=ImperalConnectorProperties)
    if hasattr(bpy, "app") and hasattr(bpy.app, "timers"):
        if not bpy.app.timers.is_registered(imperal_auto_poll_timer):
            bpy.app.timers.register(imperal_auto_poll_timer, first_interval=2.0)

def unregister():
    if not bpy: return
    if hasattr(bpy, "app") and hasattr(bpy.app, "timers"):
        if bpy.app.timers.is_registered(imperal_auto_poll_timer):
            bpy.app.timers.unregister(imperal_auto_poll_timer)
    for cls in reversed(classes): bpy.utils.unregister_class(cls)
    del bpy.types.Scene.imperal_connector

if __name__ == "__main__":
    register()

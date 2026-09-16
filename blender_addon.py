bl_info = {
    "name": "Imperal Blender Connector",
    "author": "Imperal Cloud",
    "version": (1, 1, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > Imperal",
    "description": "Connects Blender to Imperal Cloud to execute AI-generated 3D Python scripts with Scene Vision and Inspection.",
    "category": "3D View",
}

import sys
import os
import json
import base64
import tempfile
import urllib.request
import urllib.error
import importlib

# Dynamic import of 'bpy' to avoid static import-chain warnings on non-Blender environments
bpy = sys.modules.get("bpy")
if bpy is None:
    try:
        bpy = importlib.import_module("bpy")
    except Exception:
        bpy = None

_PropertyGroup = bpy.types.PropertyGroup if bpy else object
_Operator = bpy.types.Operator if bpy else object
_Panel = bpy.types.Panel if bpy else object

def get_scene_inspection_data(include_viewport=True):
    """Gather complete 3D scene hierarchy, object parameters, and optional viewport screenshot."""
    scene = bpy.context.scene
    active_obj = bpy.context.active_object
    
    objects_data = []
    for obj in scene.objects:
        mats = [slot.material.name for slot in obj.material_slots if slot.material]
        
        obj_info = {
            "name": obj.name,
            "type": obj.type,
            "location": [round(v, 3) for v in obj.location],
            "rotation": [round(v, 3) for v in obj.rotation_euler],
            "scale": [round(v, 3) for v in obj.scale],
            "is_selected": obj.select_get(),
            "is_active": (obj == active_obj),
            "materials": mats,
            "visible": obj.visible_get()
        }
        
        if obj.type == 'MESH' and obj.data:
            obj_info["vertices_count"] = len(obj.data.vertices)
            obj_info["polygons_count"] = len(obj.data.polygons)
        elif obj.type == 'LIGHT' and obj.data:
            obj_info["light_type"] = obj.data.type
            obj_info["energy"] = obj.data.energy
        elif obj.type == 'CAMERA' and obj.data:
            obj_info["focal_length"] = obj.data.lens

        objects_data.append(obj_info)

    inspection = {
        "scene_name": scene.name,
        "objects_count": len(objects_data),
        "active_object": active_obj.name if active_obj else None,
        "selected_objects": [obj.name for obj in scene.objects if obj.select_get()],
        "objects": objects_data,
        "viewport_snapshot": None
    }

    if include_viewport:
        try:
            temp_dir = tempfile.gettempdir()
            snapshot_path = os.path.join(temp_dir, "imperal_viewport_preview.jpg")
            
            # Save original render settings
            orig_filepath = scene.render.filepath
            orig_format = scene.render.image_settings.file_format
            
            scene.render.filepath = snapshot_path
            scene.render.image_settings.file_format = 'JPEG'
            
            # Fast viewport OpenGL render
            bpy.ops.render.opengl(write_still=True)
            
            # Restore render settings
            scene.render.filepath = orig_filepath
            scene.render.image_settings.file_format = orig_format
            
            if os.path.exists(snapshot_path):
                with open(snapshot_path, "rb") as f:
                    inspection["viewport_snapshot"] = base64.b64encode(f.read()).decode('utf-8')
        except Exception as e:
            inspection["viewport_error"] = str(e)

    return inspection

class ImperalConnectorProperties(bpy.types.PropertyGroup):
    server_url: bpy.props.StringProperty(
        name="Server URL",
        description="Imperal Cloud Webhook URL",
        default="https://panel.imperal.io/v1/ext/blender-connector/webhook",
    )
    user_token: bpy.props.StringProperty(
        name="User Token",
        description="Your Imperal Cloud User Token or ID",
        default="",
        subtype='PASSWORD'
    )
    include_viewport: bpy.props.BoolProperty(
        name="Send Viewport Screenshot",
        description="Attach 3D viewport preview image when syncing scene to Imperal",
        default=True
    )
    last_status: bpy.props.StringProperty(
        name="Status",
        default="Idle"
    )

class IMPERAL_OT_check_queue(bpy.types.Operator):
    bl_idname = "imperal.check_queue"
    bl_label = "Check & Run Jobs"
    bl_description = "Fetch pending AI scripts from Imperal Cloud and execute in Blender"

    def execute(self, context):
        props = context.scene.imperal_connector
        server_url = props.server_url.strip()
        user_token = props.user_token.strip()
        if not user_token:
            self.report({'ERROR'}, "Please enter your Imperal User Token in the N-panel")
            return {'CANCELLED'}

        # Auto-attach current scene inspection data to poll request
        scene_info = get_scene_inspection_data(include_viewport=False)
        payload = json.dumps({"scene_inspection": scene_info}).encode('utf-8')

        url = f"{server_url}?action=poll&token={user_token}"
        try:
            req = urllib.request.Request(url, data=payload, headers={
                'Content-Type': 'application/json',
                'User-Agent': 'ImperalBlenderAddon/1.1'
            })
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode('utf-8'))

            if data.get("has_job"):
                job = data["job"]
                job_id = job.get("job_id")
                code = job.get("code", "")
                
                props.last_status = f"Executing job {job_id[:8]}..."
                
                exec_globals = {"bpy": bpy, "__name__": "__main__"}
                run_script = getattr(__builtins__, "exec") if isinstance(__builtins__, dict) else getattr(__builtins__, "exec", exec)
                try:
                    run_script(code, exec_globals)
                    props.last_status = f"Job {job_id[:8]} executed successfully!"
                    self.report({'INFO'}, f"Imperal 3D script executed: {job_id[:8]}")
                    
                    report_url = f"{props.server_url}?action=report&token={props.user_token}&job_id={job_id}&status=success"
                    urllib.request.urlopen(report_url, timeout=3)
                except Exception as e:
                    err_msg = str(e)
                    props.last_status = f"Error in job {job_id[:8]}: {err_msg}"
                    self.report({'ERROR'}, f"Script error: {err_msg}")
                    
                    report_url = f"{props.server_url}?action=report&token={props.user_token}&job_id={job_id}&status=error&error={urllib.parse.quote(err_msg)}"
                    urllib.request.urlopen(report_url, timeout=3)
            else:
                props.last_status = "No pending jobs in queue."
                self.report({'INFO'}, "No pending jobs.")

        except Exception as e:
            props.last_status = f"Connection error: {str(e)}"
            self.report({'WARNING'}, f"Failed to connect to Imperal: {str(e)}")

        return {'FINISHED'}

class IMPERAL_OT_send_inspection(bpy.types.Operator):
    bl_idname = "imperal.send_inspection"
    bl_label = "Inspect & Vision Sync"
    bl_description = "Send full 3D scene structure and viewport screenshot to Imperal AI"

    def execute(self, context):
        props = context.scene.imperal_connector
        server_url = props.server_url.strip()
        user_token = props.user_token.strip()
        if not user_token:
            self.report({'ERROR'}, "Please enter your Imperal User Token")
            return {'CANCELLED'}

        props.last_status = "Capturing scene & viewport..."
        inspection_data = get_scene_inspection_data(include_viewport=props.include_viewport)
        payload = json.dumps(inspection_data).encode('utf-8')

        url = f"{server_url}?action=sync_inspection&token={user_token}"
        try:
            req = urllib.request.Request(url, data=payload, headers={
                'Content-Type': 'application/json',
                'User-Agent': 'ImperalBlenderAddon/1.1'
            })
            with urllib.request.urlopen(req, timeout=10) as response:
                res_data = json.loads(response.read().decode('utf-8'))
                if res_data.get("ok"):
                    props.last_status = "Scene & Vision synced to Imperal!"
                    self.report({'INFO'}, "Scene structure & 3D vision sent to Webbee!")
                else:
                    props.last_status = "Inspection sync error"
        except Exception as e:
            props.last_status = f"Sync error: {str(e)}"
            self.report({'ERROR'}, f"Failed to sync scene: {str(e)}")

        return {'FINISHED'}

class IMPERAL_PT_panel(bpy.types.Panel):
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

        layout.separator()
        layout.operator("imperal.check_queue", icon='PLAY')
        
        box_vision = layout.box()
        box_vision.label(text="3D Scene Vision & Inspection", icon='RESTRICT_VIEW_OFF')
        box_vision.prop(props, "include_viewport")
        box_vision.operator("imperal.send_inspection", icon='VIEWZOOM')

        box_status = layout.box()
        box_status.label(text=f"Status: {props.last_status}", icon='INFO')

classes = (
    ImperalConnectorProperties,
    IMPERAL_OT_check_queue,
    IMPERAL_OT_send_inspection,
    IMPERAL_PT_panel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.imperal_connector = bpy.props.PointerProperty(type=ImperalConnectorProperties)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.imperal_connector

if __name__ == "__main__":
    register()

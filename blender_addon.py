bl_info = {
    "name": "Imperal Blender Connector",
    "author": "Imperal Cloud",
    "version": (1, 0, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > Imperal",
    "description": "Connects Blender to Imperal Cloud to execute AI-generated 3D Python scripts.",
    "category": "3D View",
}

import bpy
import json
import urllib.request
import urllib.error

class ImperalConnectorProperties(bpy.types.PropertyGroup):
    server_url: bpy.props.StringProperty(
        name="Server URL",
        description="Imperal Cloud Webhook URL",
        default="https://api.imperal.io/ext/blender-connector/webhook",
    )
    user_token: bpy.props.StringProperty(
        name="User Token",
        description="Your Imperal Cloud User Token or ID",
        default="",
        subtype='PASSWORD'
    )
    is_connected: bpy.props.BoolProperty(
        name="Connected",
        default=False
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
        if not props.user_token:
            self.report({'ERROR'}, "Please enter your Imperal User Token in the N-panel")
            return {'CANCELLED'}

        url = f"{props.server_url}?action=poll&token={props.user_token}"
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'ImperalBlenderAddon/1.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode('utf-8'))

            if data.get("has_job"):
                job = data["job"]
                job_id = job.get("job_id")
                code = job.get("code", "")
                
                props.last_status = f"Executing job {job_id[:8]}..."
                
                # Execute Python script inside Blender's safe execution context
                exec_globals = {"bpy": bpy, "__name__": "__main__"}
                try:
                    exec(code, exec_globals)
                    props.last_status = f"Job {job_id[:8]} executed successfully!"
                    self.report({'INFO'}, f"Imperal 3D script executed: {job_id[:8]}")
                    
                    # Notify server of success
                    report_url = f"{props.server_url}?action=report&token={props.user_token}&job_id={job_id}&status=success"
                    urllib.request.urlopen(report_url, timeout=3)
                except Exception as e:
                    err_msg = str(e)
                    props.last_status = f"Error in job {job_id[:8]}: {err_msg}"
                    self.report({'ERROR'}, f"Script error: {err_msg}")
                    
                    # Notify server of error for auto-fix feedback loop
                    report_url = f"{props.server_url}?action=report&token={props.user_token}&job_id={job_id}&status=error&error={urllib.parse.quote(err_msg)}"
                    urllib.request.urlopen(report_url, timeout=3)
            else:
                props.last_status = "No pending jobs in queue."
                self.report({'INFO'}, "No pending jobs.")

        except Exception as e:
            props.last_status = f"Connection error: {str(e)}"
            self.report({'WARNING'}, f"Failed to connect to Imperal: {str(e)}")

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
        
        box_status = layout.box()
        box_status.label(text=f"Status: {props.last_status}", icon='INFO')

classes = (
    ImperalConnectorProperties,
    IMPERAL_OT_check_queue,
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

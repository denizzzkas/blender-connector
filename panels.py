from imperal_sdk import Extension, ui
from handlers.webhook import _JOB_STATUSES, _JOB_QUEUE

def register_panels(ext: Extension):
    @ext.panel("blender_status")
    async def render_status_panel(ctx):
        """
        Left sidebar panel showing Blender connection status and queue overview.
        """
        user_token = getattr(ctx, 'user_id', 'demo_user') or 'demo_user'
        pending_count = len(_JOB_QUEUE.get(user_token, []))

        return {
            "title": "Blender Connector",
            "components": [
                {
                    "type": "card",
                    "title": "Blender Connection Status",
                    "description": "Install the Imperal Addon in Blender to execute 3D AI scripts directly.",
                    "items": [
                        {
                            "type": "badge",
                            "label": f"Pending Jobs: {pending_count}",
                            "variant": "info" if pending_count > 0 else "neutral"
                        },
                        {
                            "type": "text",
                            "value": f"Your User Token: **{user_token}** (Enter this token in Blender N-panel)"
                        }
                    ]
                },
                {
                    "type": "button",
                    "label": "Download Blender Addon (.py)",
                    "action": "get_addon_script",
                    "variant": "primary"
                }
            ]
        }

    @ext.panel("blender_studio")
    async def render_studio_panel(ctx):
        """
        Center Studio panel with prompt form, generated code editor, and execution history.
        """
        recent_jobs = list(_JOB_STATUSES.items())[-5:]
        history_items = []
        for j_id, j_data in reversed(recent_jobs):
            history_items.append({
                "job_id": j_id,
                "prompt": j_data.get("prompt", ""),
                "status": j_data.get("status", "pending")
            })

        return {
            "title": "Blender 3D AI Studio",
            "components": [
                {
                    "type": "form",
                    "title": "Generate 3D Scene / Script",
                    "action": "generate_3d_script",
                    "fields": [
                        {
                            "name": "prompt",
                            "label": "Describe what you want to build in Blender",
                            "type": "textarea",
                            "placeholder": "e.g. A retro sci-fi computer terminal with glowing neon buttons and metallic shaders"
                        },
                        {
                            "name": "target_mode",
                            "label": "Mode",
                            "type": "select",
                            "options": [
                                {"label": "Build New Scene (Clear default mesh)", "value": "new_scene"},
                                {"label": "Modify Active Scene / Selected Object", "value": "modify_active"}
                            ],
                            "default": "new_scene"
                        }
                    ]
                },
                {
                    "type": "table",
                    "title": "Recent 3D Generation History",
                    "columns": ["Job ID", "Prompt", "Status"],
                    "rows": [
                        [item["job_id"], item["prompt"], item["status"]] for item in history_items
                    ]
                }
            ]
        }

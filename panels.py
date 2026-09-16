from imperal_sdk import Extension, ui
from handlers.webhook import _JOB_STATUSES, _JOB_QUEUE, get_scene_inspection

def register_panels(ext: Extension):
    @ext.panel("blender_status")
    async def render_status_panel(ctx):
        """
        Left sidebar panel showing Blender connection status and queue overview.
        """
        user_token = getattr(ctx, 'user_id', 'demo_user') or 'demo_user'
        pending_count = len(_JOB_QUEUE.get(user_token, []))
        inspection = get_scene_inspection(user_token)
        sync_time = "Never"
        if inspection.get("timestamp"):
            sync_time = "Just now"

        return {
            "title": "Blender Connector",
            "components": [
                {
                    "type": "card",
                    "title": "Blender Connection & Vision Status",
                    "description": "Install the Imperal Addon in Blender to execute 3D AI scripts directly and sync 3D scene vision.",
                    "items": [
                        {
                            "type": "badge",
                            "label": f"Pending Jobs: {pending_count}",
                            "variant": "info" if pending_count > 0 else "neutral"
                        },
                        {
                            "type": "badge",
                            "label": f"3D Scene Synced: {inspection.get('objects_count', 0)} objects ({sync_time})",
                            "variant": "success" if inspection.get("objects_count") else "neutral"
                        },
                        {
                            "type": "text",
                            "value": f"Your User Token: **{user_token}** (Enter this token in Blender N-panel)"
                        }
                    ]
                },
                {
                    "type": "button",
                    "label": "Inspect Active 3D Scene",
                    "action": "inspect_active_scene",
                    "variant": "secondary"
                },
                {
                    "type": "button",
                    "label": "Download Blender Addon (.py)",
                    "action": "get_addon_script",
                    "variant": "primary"
                },
                {
                    "type": "card",
                    "title": "Инструкция по установке плагина в Blender",
                    "description": "Пошаговое руководство по подключению плагина в Blender (версии 3.x и 4.x):",
                    "items": [
                        {
                            "type": "text",
                            "value": "1. Нажмите кнопку **Download Blender Addon (.py)** выше и сохраните файл `imperal_blender_connector.py`.\n2. Откройте Blender и перейдите в верхнее меню: **Edit ➔ Preferences ➔ Add-ons**.\n3. Нажмите кнопку **Install...** в верхнем углу и выберите скачанный файл `imperal_blender_connector.py`.\n4. Поставьте галочку напротив появившегося плагина **Imperal Blender Connector**.\n5. В 3D-вьюпорте Blender нажмите клавишу **N** (откроется панель справа), выберите вкладку **Imperal** и вставьте ваш **User Token**."
                        }
                    ]
                }
            ]
        }

    @ext.panel("blender_studio")
    async def render_studio_panel(ctx):
        """
        Center Studio panel with prompt form, generated code editor, and execution history.
        """
        user_token = getattr(ctx, 'user_id', 'demo_user') or 'demo_user'
        recent_jobs = list(_JOB_STATUSES.items())[-5:]
        history_items = []
        for j_id, j_data in reversed(recent_jobs):
            history_items.append({
                "job_id": j_id,
                "prompt": j_data.get("prompt", ""),
                "status": j_data.get("status", "pending")
            })

        inspection = get_scene_inspection(user_token)

        return {
            "title": "Blender 3D AI Studio",
            "components": [
                {
                    "type": "card",
                    "title": f"Active Blender 3D Scene: {inspection.get('scene_name', 'Not Synced Yet')}",
                    "description": f"Objects: {inspection.get('objects_count', 0)} | Active: {inspection.get('active_object', 'None')} | Selected: {', '.join(inspection.get('selected_objects', [])) or 'None'}"
                },
                {
                    "type": "form",
                    "title": "Generate 3D Scene / Script",
                    "action": "generate_3d_script",
                    "fields": [
                        {
                            "name": "prompt",
                            "label": "Describe what you want to build or modify in Blender",
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

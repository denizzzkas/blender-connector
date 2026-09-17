from __future__ import annotations

from imperal_sdk import Extension, ui
from app import ext
from handlers.webhook import _JOB_STATUSES, _JOB_QUEUE, get_scene_inspection


@ext.panel(
    "blender_status",
    slot="left",
    title="Blender Connector",
    icon="Box",
    refresh="manual",
    default_width=320,
    min_width=280,
)
async def render_status_panel(ctx) -> ui.UINode:
    """
    Left sidebar panel showing Blender connection status, download button, and step-by-step instructions.
    """
    user_token = (
        getattr(ctx, 'user_id', None)
        or getattr(getattr(ctx, 'user', None), 'imperal_id', None)
        or 'demo_user'
    )
    pending_count = len(_JOB_QUEUE.get(user_token, []))
    inspection = await get_scene_inspection(user_token, ctx)
    sync_time = "Never"
    if inspection.get("timestamp"):
        sync_time = "Just now"

    objects_count = inspection.get("objects_count", 0)
    connected_badge = (
        ui.Alert(
            title="Blender Connected",
            message=f"3D Scene Synced: {objects_count} objects ({sync_time})",
            type="info" if objects_count > 0 else "info",
        )
        if objects_count > 0
        else ui.Alert(
            title="Blender Not Connected",
            message="Install the Imperal Addon in Blender to execute 3D AI scripts directly and sync scene vision.",
            type="info",
        )
    )

    token_card = ui.Card(
        title="Your Connection Token",
        content=ui.Stack([
            ui.Text(content=f"User Token: **{user_token}**", variant="body"),
            ui.Text(content="Enter this token in the Blender N-panel under the **Imperal** tab.", variant="caption"),
        ]),
    )

    addon_url = f"https://panel.imperal.io/v1/ext/{ext.app_id}/webhook/download"
    if hasattr(ctx, "webhook_url"):
        try:
            addon_url = ctx.webhook_url("/download")
        except Exception:
            pass

    addon_button = ui.Button(
        label="Download Blender Addon (.py)",
        variant="primary",
        full_width=True,
        icon="Download",
        on_click=ui.Open(addon_url),
    )

    inspect_button = ui.Button(
        label="Inspect Active 3D Scene",
        variant="secondary",
        full_width=True,
        icon="Eye",
        on_click=ui.Call("inspect_active_scene"),
    )

    instructions_card = ui.Card(
        title="Plugin Installation Instructions",
        content=ui.Markdown(
            content=(
                "1. Click the **Download Blender Addon (.py)** button above to save `imperal_blender_connector.py`.\n\n"
                "2. Open Blender and navigate to top menu: **Edit ➔ Preferences ➔ Add-ons**.\n\n"
                "3. Click **Install...** in the top right corner and select the downloaded file.\n\n"
                "4. Enable the checkbox for **Imperal Blender Connector**.\n\n"
                "5. In the Blender 3D Viewport, press **N** to expand the right sidebar, open the **Imperal** tab, and enter your **User Token**."
            )
        ),
    )

    return ui.Stack([
        ui.Header("Blender Connector", level=3, subtitle="AI 3D Scene Generator & Inspector"),
        connected_badge,
        token_card,
        addon_button,
        inspect_button,
        ui.Divider("Instructions"),
        instructions_card,
    ])


@ext.panel("blender_studio", slot="center", title="Blender 3D AI Studio")
async def render_studio_panel(ctx) -> ui.UINode:
    """
    Center Studio panel with prompt form, generated code editor, and execution history.
    """
    user_token = (
        getattr(ctx, 'user_id', None)
        or getattr(getattr(ctx, 'user', None), 'imperal_id', None)
        or 'demo_user'
    )
    recent_jobs = list(_JOB_STATUSES.items())[-5:]
    history_rows = []
    for j_id, j_data in reversed(recent_jobs):
        history_rows.append({
            "job_id": j_id[:8],
            "prompt": j_data.get("prompt", ""),
            "status": j_data.get("status", "pending"),
        })

    inspection = await get_scene_inspection(user_token, ctx)

    viewport_snapshot = inspection.get("viewport_snapshot")
    viewport_widget = (
        ui.Image(src=viewport_snapshot, alt="3D Viewport Preview", width="100%", caption="3D Viewport Live Sync")
        if viewport_snapshot
        else ui.Text(content="*No viewport screenshot synced yet. Enable 'Send Viewport Screenshot' in Blender N-panel.*", variant="caption")
    )

    scene_card = ui.Card(
        title=f"Active Scene Vision: {inspection.get('scene_name', 'Not Synced Yet')}",
        content=ui.Stack([
            ui.Text(
                content=(
                    f"**Objects:** {inspection.get('objects_count', 0)} | "
                    f"**Active:** {inspection.get('active_object', 'None')} | "
                    f"**Selected:** {', '.join(inspection.get('selected_objects', [])) or 'None'}"
                ),
                variant="body",
            ),
            viewport_widget,
        ]),
    )

    history_table = ui.DataTable(
        columns=[
            {"key": "job_id", "label": "Job ID"},
            {"key": "prompt", "label": "Prompt"},
            {"key": "status", "label": "Status"},
        ],
        rows=history_rows,
    )

    return ui.Stack([
        ui.Header("Blender 3D AI Studio", level=2, subtitle="Center workspace for 3D generation and history"),
        scene_card,
        ui.Divider("History"),
        history_table,
    ])


def register_panels(ext_obj: Extension):
    pass

from imperal_sdk import Extension, ChatExtension
from tools import handle_generate_3d_script, handle_get_addon_script
from handlers.webhook import register_webhook_handlers
from panels import register_panels

ext = Extension(
    "blender-connector",
    version="1.0.0",
    display_name="Blender Connector",
    description="AI 3D Scene Generator for Blender via Imperal Cloud.",
    icon="icon.svg",
    actions_explicit=True,
    capabilities=["blender-connector:generate", "blender-connector:read"],
)

chat = ChatExtension(
    ext,
    tool_name="blender_connector",
    description="Blender Connector — AI 3D scene generation and Blender execution integration.",
)

@ext.action("generate_3d_script")
async def generate_3d_script(ctx, params: dict):
    return await handle_generate_3d_script(ctx, params)

@ext.action("get_addon_script")
async def get_addon_script(ctx, params: dict):
    return await handle_get_addon_script(ctx, params)

register_webhook_handlers(ext)
register_panels(ext)

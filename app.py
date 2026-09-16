from imperal_sdk import Extension, ChatExtension

ext = Extension(
    "blender-connector",
    version="1.1.0",
    display_name="Blender Connector",
    description="AI 3D Scene Generator and Inspector for Blender via Imperal Cloud.",
    icon="icon.svg",
    actions_explicit=True,
    capabilities=["blender-connector:generate", "blender-connector:read"],
)

chat = ChatExtension(
    ext,
    tool_name="blender_connector",
    description="Blender Connector — AI 3D scene generation, inspection, viewport vision, and Blender execution integration.",
)

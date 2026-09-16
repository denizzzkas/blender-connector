# Changelog

All notable changes to the **Blender Connector** extension will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.1.0] - 2026-09-16

### Added
- 👁️ **3D Scene Inspection**: New tool `inspect_active_scene` to inspect 3D object hierarchy, locations, rotations, scales, polygons, materials, camera settings, and light setups.
- 📸 **3D Viewport Vision**: Added OpenGL viewport snapshot capture to the Blender addon, allowing Webbee to "see" real-time 3D viewport renders.
- 🎛️ **Sync 3D Scene Vision Button**: Dedicated UI trigger in Blender N-panel to manually force immediate scene and vision sync.
- 📖 **Addon Installation Guide**: Added interactive step-by-step installation instructions directly inside the Imperal left status panel.
- 🧪 **Expanded Test Suite**: Comprehensive tests covering `generate_3d_script`, `inspect_active_scene`, `get_addon_script`, webhook endpoints (`poll`, `sync_inspection`, `result`), panels rendering, and manifest validation.

### Changed
- Updated manifest version to `1.1.0` and SDK version to `5.9.13`.
- Improved procedural `bpy` script generator with fallback handling for cylinders, spheres, and complex objects.

---

## [1.0.0] - 2026-09-11

### Added
- 🚀 Initial release of **Blender Connector**.
- 🪄 Text-to-3D (`bpy`) Python script generation tool (`generate_3d_script`).
- 🔌 Standalone Blender Addon (`blender_addon.py`) with background polling (`bpy.app.timers`).
- 🌐 Webhook Relay (`/webhook`) for job polling and result reporting.
- 🖥️ Imperal RPC Panels (`blender_status` and `blender_studio`).

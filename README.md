# 🎨 Blender Connector for Imperal Cloud

[![Imperal Cloud](https://img.shields.io/badge/Imperal%20Cloud-Extension-F5792A?style=for-the-badge&logo=cloud&logoColor=white)](https://imperal.io)
[![Blender Version](https://img.shields.io/badge/Blender-3.0%2B%20%7C%204.x-E87D0D?style=for-the-badge&logo=blender&logoColor=white)](https://www.blender.org)
[![Python Version](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![License: LGPL v3](https://img.shields.io/badge/License-LGPL%20v3-blue.svg?style=for-the-badge)](LICENSE)

**Blender Connector** bridges **Imperal Cloud's Agentic AI Brain** (`Webbee`) directly with your local **Blender 3D** graphics editor. Generate procedural 3D meshes, materials, lighting setups, and full scenes using plain natural language prompts — complete with real-time **3D Scene Inspection** and **Viewport Vision**.

---

## ✨ Features

- 🪄 **Natural Language to 3D (`bpy`)**: Converts text prompts into clean, executable Blender Python scripts (`bpy`).
- 👁️ **3D Scene Inspection**: Webbee inspects your active Blender scene hierarchy, object locations, materials, polygons, lights, and camera settings.
- 📸 **3D Viewport Vision**: Captures and syncs real-time OpenGL viewport screenshots from Blender so the AI can "see" your 3D viewport.
- ⚡ **Seamless Relay Sync**: Lightweight background polling (`bpy.app.timers`) executes AI scripts inside Blender instantly without blocking the UI.
- 🔄 **Auto-Repair Loop**: Automatically reports execution errors back to Imperal so Webbee can fix broken code on the fly.
- 🎛️ **Imperal RPC Studio Panel**: View job queues, edit generated code, download the addon, and track generation history directly from your Imperal Cloud panel.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    1. Imperal Extension                         │
│  - AI Tools (generate_3d_script, inspect_active_scene)          │
│  - RPC Panels (blender_status, blender_studio)                  │
│  - Webhook Relay Queue (/webhook)                               │
└─────────────────────────────────┬───────────────────────────────┘
                                  │ HTTPS / JSON / Base64 Vision
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                     2. Blender Addon (.py)                      │
│  - Installed in Blender (View3D > Sidebar > Imperal)            │
│  - Background polling (bpy.app.timers)                          │
│  - Scene hierarchy scanner & Viewport Screenshot renderer       │
│  - Safe main-thread script execution                             │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start & Installation

### 1. Download the Addon
In your Imperal Cloud panel, navigate to **Blender Connector** and click **"Download Blender Addon (.py)"** (or download `blender_addon.py` directly from this repository).

### 2. Install in Blender
1. Open Blender (3.0+ or 4.x).
2. Go to **Edit ➔ Preferences ➔ Add-ons**.
3. Click **Install...** in the top right corner and select `imperal_blender_connector.py` (or `blender_addon.py`).
4. Enable the checkbox next to **Imperal Blender Connector**.

### 3. Connect to Imperal
1. In the Blender 3D Viewport, press **N** to toggle the sidebar.
2. Select the **Imperal** tab.
3. Paste your **User Token** (found in your Imperal panel) into the token field.
4. Enable **Auto-run Queue** or click **Sync 3D Scene Vision**.

---

## 🛠️ Tools Reference

| Tool | Action Type | Description |
| :--- | :--- | :--- |
| `generate_3d_script` | `write` | Generates a Blender Python (`bpy`) script based on a prompt to create or modify 3D scenes. |
| `inspect_active_scene` | `read` | Retrieves the active Blender scene hierarchy, materials, camera, and viewport snapshot. |
| `get_addon_script` | `read` | Provides the standalone Python addon source code for installation. |

---

## 🧪 Running Tests

Run the test suite locally using `pytest`:

```bash
PYTHONPATH=. python3 -m pytest -v
```

---

## 📄 License

Distributed under the **GNU Lesser General Public License v3.0 (LGPL-3.0)**. See [`LICENSE`](LICENSE) for details.

"""Blender Connector — Imperal Cloud extension entrypoint.

Connects Blender 3D with Imperal Cloud for AI-driven 3D scene generation,
inspection, viewport vision, and execution.
"""
from __future__ import annotations

import os
import sys

_dir = os.path.dirname(os.path.abspath(__file__))
if _dir not in sys.path:
    sys.path.insert(0, _dir)

_MODULES_TO_RELOAD = (
    "app",
    "tools",
    "panels",
    "handlers",
    "handlers.generate",
    "handlers.webhook",
)

for _m in _MODULES_TO_RELOAD:
    if _m in sys.modules:
        del sys.modules[_m]

from app import ext, chat  # noqa: F401
from handlers.webhook import register_webhook_handlers
import tools  # noqa: F401
import panels  # noqa: F401

register_webhook_handlers(ext)

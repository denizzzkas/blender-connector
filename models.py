"""Blender Connector — Pydantic param and result models for chat tools."""
from __future__ import annotations

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class Generate3DParams(BaseModel):
    prompt: str = Field(
        description="Description of the 3D scene, object, material, or animation to create in Blender."
    )
    target_mode: str = Field(
        default="new_scene",
        description="Generation mode: 'new_scene' (clears default mesh and builds fresh) or 'modify_active' (modifies current scene/selected object)."
    )


class Generate3DResult(BaseModel):
    job_id: str = Field(description="Unique job identifier for tracking execution in Blender")
    status: str = Field(description="Status of job submission ('pending_blender')")
    code: str = Field(description="Generated Blender Python script (bpy)")
    explanation: str = Field(description="Plain text explanation of how the script was constructed")


class InspectSceneParams(BaseModel):
    include_viewport: bool = Field(
        default=True,
        description="Whether to include a base64 encoded viewport JPEG snapshot."
    )


class InspectSceneResult(BaseModel):
    scene_name: str = Field(default="Scene", description="Name of the active scene in Blender")
    objects_count: int = Field(default=0, description="Total number of objects in the active scene")
    active_object: Optional[str] = Field(default=None, description="Name of the active object, if any")
    selected_objects: List[str] = Field(default_factory=list, description="Names of selected objects")
    objects: List[Dict[str, Any]] = Field(default_factory=list, description="List of object parameter details")
    viewport_snapshot: Optional[str] = Field(default=None, description="Base64 encoded JPEG viewport screenshot if available")
    message: Optional[str] = Field(default=None, description="Informational or warning message if sync is missing")


class GetAddonParams(BaseModel):
    pass


class GetAddonResult(BaseModel):
    filename: str = Field(description="Filename of the Blender Python addon script")
    addon_code: str = Field(description="Complete source code of the standalone Blender addon")
    version: str = Field(description="Version of the addon script")

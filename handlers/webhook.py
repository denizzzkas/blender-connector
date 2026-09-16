import json
import time
import urllib.parse
from imperal_sdk import Extension

# In-memory/store queue for pending jobs per user token
_JOB_QUEUE = {}
_JOB_STATUSES = {}
_USER_SCENE_INSPECTION = {}

def queue_job_for_user(user_token: str, job_data: dict):
    if user_token not in _JOB_QUEUE:
        _JOB_QUEUE[user_token] = []
    _JOB_QUEUE[user_token].append(job_data)
    _JOB_STATUSES[job_data["job_id"]] = {
        "status": "pending_blender",
        "created_at": time.time(),
        "prompt": job_data.get("prompt", ""),
        "explanation": job_data.get("explanation", "")
    }

def get_job_status(job_id: str) -> dict:
    return _JOB_STATUSES.get(job_id, {"status": "unknown"})

def store_scene_inspection(user_token: str, data: dict):
    _USER_SCENE_INSPECTION[user_token] = {
        "timestamp": time.time(),
        "scene_name": data.get("scene_name", "Scene"),
        "objects_count": data.get("objects_count", 0),
        "active_object": data.get("active_object"),
        "selected_objects": data.get("selected_objects", []),
        "objects": data.get("objects", []),
        "viewport_snapshot": data.get("viewport_snapshot")
    }

def get_scene_inspection(user_token: str) -> dict:
    return _USER_SCENE_INSPECTION.get(user_token, {})

def register_webhook_handlers(ext: Extension):
    @ext.webhook("/webhook")
    async def handle_blender_webhook(ctx, req):
        """
        Webhook endpoint called by Blender Addon to poll for jobs, sync scene inspection, and report execution results.
        """
        query = getattr(req, 'query_params', {})
        action = query.get("action", "poll")
        token = query.get("token", "")

        if not token:
            return {
                "status_code": 400,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "Missing token parameter"})
            }

        if action == "poll":
            user_jobs = _JOB_QUEUE.get(token, [])
            if user_jobs:
                job = user_jobs.pop(0) # Pop oldest job
                _JOB_STATUSES[job["job_id"]]["status"] = "executing_in_blender"
                return {
                    "status_code": 200,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps({"has_job": True, "job": job})
                }
            return {
                "status_code": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"has_job": False})
            }

        elif action == "sync_inspection":
            try:
                raw_body = getattr(req, 'body', b'')
                if isinstance(raw_body, bytes):
                    raw_body = raw_body.decode('utf-8')
                data = json.loads(raw_body) if raw_body else {}
                store_scene_inspection(token, data)
                return {
                    "status_code": 200,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps({"ok": True, "message": "Scene & vision synced"})
                }
            except Exception as e:
                return {
                    "status_code": 400,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps({"error": f"Invalid inspection payload: {str(e)}"})
                }

        elif action == "report":
            job_id = query.get("job_id", "")
            status = query.get("status", "success")
            error = query.get("error", "")

            if job_id in _JOB_STATUSES:
                _JOB_STATUSES[job_id]["status"] = status
                if error:
                    _JOB_STATUSES[job_id]["error"] = urllib.parse.unquote(error)

            return {
                "status_code": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"ok": True, "job_id": job_id, "status": status})
            }

        return {
            "status_code": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": f"Unknown action '{action}'"})
        }

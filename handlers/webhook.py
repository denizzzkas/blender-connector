import json
import time
from imperal_sdk import Extension

# In-memory/store queue for pending jobs per user token
_JOB_QUEUE = {}
_JOB_STATUSES = {}

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

def register_webhook_handlers(ext: Extension):
    @ext.webhook("/webhook")
    async def handle_blender_webhook(ctx, req):
        """
        Webhook endpoint called by Blender Addon to poll for jobs and report execution results.
        URL format: /ext/blender-connector/webhook?action=poll&token=<token>
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

        elif action == "result":
            job_id = query.get("job_id", "")
            status = query.get("status", "success")
            error_msg = query.get("error", "")
            if job_id in _JOB_STATUSES:
                _JOB_STATUSES[job_id]["status"] = status
                _JOB_STATUSES[job_id]["error"] = error_msg
            return {
                "status_code": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"ok": True})
            }

        return {
            "status_code": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "Invalid action"})
        }

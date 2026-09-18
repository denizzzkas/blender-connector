import json
import time
import urllib.parse
from imperal_sdk import Extension

# In-memory fallback queue for pending jobs per user token
_JOB_QUEUE = {}
_JOB_STATUSES = {}
_USER_SCENE_INSPECTION = {}
BLENDER_SCENE_COLLECTION = "blender_scenes"
BLENDER_JOBS_COLLECTION = "blender_jobs"

async def queue_job_for_user(user_token: str, job_data: dict, ctx=None):
    # Replace pending queue with the latest job to avoid executing stale older jobs
    _JOB_QUEUE[user_token] = [job_data]
    _JOB_STATUSES[job_data["job_id"]] = {
        "status": "pending_blender",
        "created_at": time.time(),
        "prompt": job_data.get("prompt", ""),
        "explanation": job_data.get("explanation", "")
    }

    if ctx and hasattr(ctx, "store") and ctx.store:
        try:
            job_record = dict(job_data)
            job_record["user_token"] = user_token
            job_record["status"] = "pending"
            job_record["created_at"] = time.time()
            store = ctx.store.for_user(user_token) if hasattr(ctx.store, "for_user") else ctx.store
            await store.create(BLENDER_JOBS_COLLECTION, job_record)
        except Exception:
            pass

def get_job_status(job_id: str) -> dict:
    return _JOB_STATUSES.get(job_id, {"status": "unknown"})

async def store_scene_inspection(user_token: str, data: dict, ctx=None):
    prev = _USER_SCENE_INSPECTION.get(user_token, {})
    new_snapshot = data.get("viewport_snapshot")
    # Preserve existing snapshot if new poll payload does not include one
    if not new_snapshot and prev.get("viewport_snapshot"):
        new_snapshot = prev.get("viewport_snapshot")

    inspection_record = {
        "timestamp": time.time(),
        "scene_name": data.get("scene_name", prev.get("scene_name", "Scene")),
        "objects_count": data.get("objects_count", prev.get("objects_count", 0)),
        "active_object": data.get("active_object", prev.get("active_object")),
        "selected_objects": data.get("selected_objects", prev.get("selected_objects", [])),
        "objects": data.get("objects", prev.get("objects", [])),
        "viewport_snapshot": new_snapshot,
        "viewport_error": data.get("viewport_error")
    }
    _USER_SCENE_INSPECTION[user_token] = inspection_record

    if ctx and hasattr(ctx, "store") and ctx.store:
        try:
            record_with_user = dict(inspection_record)
            record_with_user["user_token"] = user_token
            store = ctx.store.for_user(user_token) if hasattr(ctx.store, "for_user") else ctx.store
            page = await store.query(BLENDER_SCENE_COLLECTION)
            if page and getattr(page, "data", None) and len(page.data) > 0:
                doc_id = page.data[0].id
                await store.update(BLENDER_SCENE_COLLECTION, doc_id, record_with_user)
            else:
                await store.create(BLENDER_SCENE_COLLECTION, record_with_user)
        except Exception:
            pass

async def get_scene_inspection(user_token: str, ctx=None) -> dict:
    if user_token in _USER_SCENE_INSPECTION:
        return _USER_SCENE_INSPECTION[user_token]

    if ctx and hasattr(ctx, "store") and ctx.store:
        try:
            store = ctx.store.for_user(user_token) if hasattr(ctx.store, "for_user") else ctx.store
            page = await store.query(BLENDER_SCENE_COLLECTION)
            if page and getattr(page, "data", None) and len(page.data) > 0:
                rec = page.data[0]
                rec_dict = rec.data if hasattr(rec, "data") else (rec.to_dict() if hasattr(rec, "to_dict") else dict(rec))
                _USER_SCENE_INSPECTION[user_token] = rec_dict
                return rec_dict
        except Exception:
            pass

    return _USER_SCENE_INSPECTION.get(user_token, {})

def register_webhook_handlers(ext: Extension):
    @ext.webhook("/download", method="GET")
    async def handle_download_webhook(ctx, headers=None, body=None, query_params=None, **kwargs):
        """
        Public GET endpoint to download the Blender addon Python script directly.
        """
        import os
        script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "blender_addon.py")
        if not os.path.exists(script_path):
            return {
                "status_code": 404,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "blender_addon.py not found on disk"})
            }
        with open(script_path, "r", encoding="utf-8") as f:
            content = f.read()
        return {
            "status_code": 200,
            "headers": {
                "Content-Type": "text/x-python-script; charset=utf-8",
                "Content-Disposition": 'attachment; filename="imperal_blender_connector.py"'
            },
            "body": content
        }

    @ext.webhook("", method="POST")
    @ext.webhook("/webhook", method="POST")
    async def handle_blender_webhook(ctx, headers=None, body=None, query_params=None, **kwargs):
        """
        Webhook endpoint called by Blender Addon to poll for jobs, sync scene inspection, and report execution results.
        """
        query = query_params or {}
        if not query and hasattr(headers, "query_params"): # backwards compat if req passed
            query = getattr(headers, "query_params", {})
        action = query.get("action", "poll")
        token = query.get("token", "").strip()

        if not token:
            return {
                "status_code": 400,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "Missing token parameter"})
            }

        if action == "poll":
            try:
                raw_body = body or query.get("data", "")
                if isinstance(raw_body, bytes):
                    raw_body = raw_body.decode('utf-8')
                if isinstance(raw_body, dict):
                    data = raw_body
                elif isinstance(raw_body, str) and raw_body.strip():
                    data = json.loads(raw_body)
                else:
                    data = {}
                if isinstance(data, dict) and "scene_inspection" in data:
                    await store_scene_inspection(token, data["scene_inspection"], ctx)
            except Exception:
                pass

            user_jobs = _JOB_QUEUE.get(token, [])
            if user_jobs:
                job = user_jobs.pop(0) # Pop latest job
                _JOB_QUEUE[token] = [] # Clear memory queue so it doesn't re-run
                _JOB_STATUSES[job["job_id"]]["status"] = "executing_in_blender"
                
                # Also clean up DB pending jobs for this user so DB polling won't re-run old jobs
                if ctx and hasattr(ctx, "store") and ctx.store:
                    try:
                        store = ctx.store.for_user(token) if hasattr(ctx.store, "for_user") else ctx.store
                        page = await store.query(BLENDER_JOBS_COLLECTION, where={"status": "pending"})
                        if page and getattr(page, "data", None):
                            for doc in page.data:
                                doc_job_id = getattr(doc, "data", {}).get("job_id") if hasattr(doc, "data") else doc.get("job_id")
                                if doc_job_id != job["job_id"]:
                                    await store.update(BLENDER_JOBS_COLLECTION, doc.id, {"status": "superseded"})
                                else:
                                    await store.update(BLENDER_JOBS_COLLECTION, doc.id, {"status": "executing_in_blender"})
                    except Exception:
                        pass

                return {
                    "status_code": 200,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps({"has_job": True, "job": job})
                }

            if ctx and hasattr(ctx, "store") and ctx.store:
                try:
                    store = ctx.store.for_user(token) if hasattr(ctx.store, "for_user") else ctx.store
                    page = await store.query(BLENDER_JOBS_COLLECTION, where={"status": "pending"})
                    if page and getattr(page, "data", None) and len(page.data) > 0:
                        # Grab the latest pending job and mark all older ones as superseded
                        docs = page.data
                        latest_doc = docs[-1]
                        for doc in docs[:-1]:
                            await store.update(BLENDER_JOBS_COLLECTION, doc.id, {"status": "superseded"})
                        
                        doc_id = latest_doc.id
                        job = latest_doc.data if hasattr(latest_doc, "data") else (latest_doc.to_dict() if hasattr(latest_doc, "to_dict") else dict(latest_doc))
                        await store.update(BLENDER_JOBS_COLLECTION, doc_id, {"status": "executing_in_blender"})
                        _JOB_STATUSES[job.get("job_id", "")] = {"status": "executing_in_blender"}
                        return {
                            "status_code": 200,
                            "headers": {"Content-Type": "application/json"},
                            "body": json.dumps({"has_job": True, "job": job})
                        }
                except Exception:
                    pass

            return {
                "status_code": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"has_job": False})
            }

        elif action == "sync_inspection":
            try:
                raw_body = body or query.get("data", "")
                if isinstance(raw_body, bytes):
                    raw_body = raw_body.decode('utf-8')
                if isinstance(raw_body, dict):
                    data = raw_body
                elif isinstance(raw_body, str) and raw_body.strip():
                    data = json.loads(raw_body)
                else:
                    data = {}
                await store_scene_inspection(token, data, ctx)
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

        elif action in ("report", "result"):
            job_id = query.get("job_id", "")
            status = query.get("status", "success")
            error = query.get("error", "")
            stdout_log = ""
            stderr_log = ""

            # Extract json body if posted
            try:
                raw_body = body or query.get("data", "")
                if isinstance(raw_body, bytes): raw_body = raw_body.decode('utf-8')
                if isinstance(raw_body, dict):
                    rep_data = raw_body
                elif isinstance(raw_body, str) and raw_body.strip():
                    rep_data = json.loads(raw_body)
                else:
                    rep_data = {}
                if isinstance(rep_data, dict):
                    job_id = rep_data.get("job_id", job_id)
                    status = rep_data.get("status", status)
                    error = rep_data.get("error", error)
                    stdout_log = rep_data.get("stdout", "")
                    stderr_log = rep_data.get("stderr", "")
            except Exception:
                pass

            if job_id in _JOB_STATUSES:
                _JOB_STATUSES[job_id]["status"] = status
                if error:
                    _JOB_STATUSES[job_id]["error"] = urllib.parse.unquote(error) if isinstance(error, str) else str(error)
                if stdout_log:
                    _JOB_STATUSES[job_id]["stdout"] = stdout_log
                if stderr_log:
                    _JOB_STATUSES[job_id]["stderr"] = stderr_log

            if ctx and hasattr(ctx, "store") and ctx.store and job_id:
                try:
                    store = ctx.store.for_user(token) if (token and hasattr(ctx.store, "for_user")) else ctx.store
                    page = await store.query(BLENDER_JOBS_COLLECTION, where={"job_id": job_id})
                    if page and getattr(page, "data", None) and len(page.data) > 0:
                        doc_id = page.data[0].id
                        update_payload = {
                            "status": status,
                            "error": urllib.parse.unquote(error) if (isinstance(error, str) and error) else "",
                            "updated_at": time.time()
                        }
                        if stdout_log: update_payload["stdout"] = stdout_log
                        if stderr_log: update_payload["stderr"] = stderr_log
                        await store.update(BLENDER_JOBS_COLLECTION, doc_id, update_payload)
                except Exception:
                    pass

            return {
                "status_code": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"ok": True, "job_id": job_id, "status": status})
            }

        elif action == "download":
            script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "blender_addon.py")
            if not os.path.exists(script_path):
                return {
                    "status_code": 444,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps({"error": "blender_addon.py not found on disk"})
                }
            with open(script_path, "r", encoding="utf-8") as f:
                content = f.read()
            return {
                "status_code": 200,
                "headers": {
                    "Content-Type": "text/x-python-script; charset=utf-8",
                    "Content-Disposition": 'attachment; filename="imperal_blender_connector.py"'
                },
                "body": content
            }

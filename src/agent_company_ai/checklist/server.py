"""Z-Dot Team Checklist Portal - FastAPI app with JSON persistence."""
from __future__ import annotations

import json
import os
import shutil
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

STATIC_DIR = Path(__file__).parent / "static"
DATA_DIR = Path(__file__).parent / "data"
DATA_FILE = DATA_DIR / "checklist.json"

VALID_STATUSES = {"pending", "assigned", "in_progress", "review", "done", "failed", "cancelled"}

app = FastAPI(title="Z-Dot Team Checklist")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load() -> list[dict]:
    if not DATA_FILE.exists():
        return []
    return json.loads(DATA_FILE.read_text())


def _save(tasks: list[dict]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(DATA_DIR), suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(tasks, f, indent=2)
        os.replace(tmp, DATA_FILE)
    except Exception:
        os.unlink(tmp)
        raise


class TaskIn(BaseModel):
    description: str
    assignee: str | None = None
    priority: int = 0
    blocker: str | None = None


class TaskPatch(BaseModel):
    status: str | None = None
    assignee: str | None = None
    description: str | None = None
    result: str | None = None
    blocker: str | None = None
    last_checked_at: str | None = None


@app.get("/")
async def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/tasks")
async def list_tasks():
    return _load()


@app.post("/api/tasks", status_code=201)
async def create_task(body: TaskIn):
    if not body.description or not body.description.strip():
        raise HTTPException(400, "description is required")
    tasks = _load()
    task = {
        "id": uuid.uuid4().hex[:12],
        "description": body.description.strip(),
        "assignee": body.assignee,
        "priority": body.priority,
        "status": "assigned" if body.assignee else "pending",
        "result": None,
        "blocker": body.blocker,
        "created_at": _now(),
        "updated_at": _now(),
        "last_checked_at": None,
    }
    tasks.append(task)
    _save(tasks)
    return task


@app.patch("/api/tasks/{task_id}")
async def patch_task(task_id: str, body: TaskPatch):
    tasks = _load()
    for t in tasks:
        if t["id"] == task_id:
            if body.status is not None:
                if body.status not in VALID_STATUSES:
                    raise HTTPException(400, f"invalid status: {body.status}")
                t["status"] = body.status
            if body.assignee is not None:
                t["assignee"] = body.assignee
            if body.description is not None:
                if not body.description.strip():
                    raise HTTPException(400, "description cannot be empty")
                t["description"] = body.description.strip()
            if body.result is not None:
                t["result"] = body.result
            if body.blocker is not None:
                t["blocker"] = body.blocker
            if body.last_checked_at is not None:
                t["last_checked_at"] = body.last_checked_at
            t["updated_at"] = _now()
            _save(tasks)
            return t
    raise HTTPException(404, f"no task with id {task_id}")


@app.delete("/api/tasks/{task_id}", status_code=204)
async def delete_task(task_id: str):
    tasks = _load()
    remaining = [t for t in tasks if t["id"] != task_id]
    if len(remaining) == len(tasks):
        raise HTTPException(404, f"no task with id {task_id}")
    _save(remaining)
    return JSONResponse(status_code=204, content=None)

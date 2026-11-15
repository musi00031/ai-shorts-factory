import asyncio
import uuid
from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, Header, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel, Field

from app import db
from app.config import API_KEY
from app.agents import build_plan
from app.renderer import render_video

app = FastAPI(title="AI Shorts Factory", version="0.2.0")
db.init_db()


class JobRequest(BaseModel):
    topic: str = Field(min_length=2, max_length=300)
    script: str = Field(default="", max_length=6000)
    language: str = Field(default="ru", max_length=12)
    duration: int = Field(default=35, ge=10, le=90)


def require_auth(authorization: str | None) -> None:
    # Fail closed: never expose job creation/history/video without a configured key.
    if not API_KEY:
        raise HTTPException(status_code=503, detail="Server is not configured: set API_KEY")
    if authorization != f"Bearer {API_KEY}":
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


async def process(job_id: str) -> None:
    job = db.get_job(job_id)
    if not job:
        return
    try:
        db.update_job(job_id, status="planning")
        plan = build_plan(job["payload"])
        db.update_job(job_id, status="rendering", result={"plan": plan})
        path = await asyncio.to_thread(render_video, job_id, plan, job["duration"])
        db.update_job(job_id, status="completed", result={"plan": plan, "video_path": path})
    except Exception as exc:
        db.update_job(job_id, status="failed", error=repr(exc))


@app.get("/health")
def health():
    return {"ok": True, "service": "ai-shorts-factory"}


@app.get("/", response_class=HTMLResponse)
def home():
    return Path("web/index.html").read_text(encoding="utf-8")


@app.post("/api/jobs")
def create(
    body: JobRequest,
    background_tasks: BackgroundTasks,
    authorization: str | None = Header(default=None),
):
    require_auth(authorization)
    job_id = uuid.uuid4().hex[:12]
    db.add_job(job_id, body.model_dump())
    background_tasks.add_task(process, job_id)
    return {"id": job_id, "status": "queued"}


@app.get("/api/jobs")
def jobs(limit: int = 30, authorization: str | None = Header(default=None)):
    require_auth(authorization)
    return {"jobs": db.list_jobs(max(1, min(limit, 100)))}


@app.get("/api/jobs/{job_id}")
def status(job_id: str, authorization: str | None = Header(default=None)):
    require_auth(authorization)
    job = db.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.get("/api/jobs/{job_id}/video")
def video(job_id: str, authorization: str | None = Header(default=None)):
    require_auth(authorization)
    job = db.get_job(job_id)
    result = (job or {}).get("result") or {}
    path = result.get("video_path")
    if not path or not Path(path).is_file():
        raise HTTPException(status_code=404, detail="Video not ready")
    return FileResponse(path, media_type="video/mp4", filename=f"short-{job_id}.mp4")

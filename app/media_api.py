import uuid
from pathlib import Path
from fastapi import APIRouter, BackgroundTasks, Header, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from app.config import API_KEY
from app import media_db
from app.media_pipeline import run_pipeline

router = APIRouter()
media_db.init_media_db()

def auth(value):
    if not API_KEY:
        raise HTTPException(status_code=503, detail="Server is not configured: set API_KEY")
    if value != f"Bearer {API_KEY}":
        raise HTTPException(status_code=401, detail="Invalid or missing API key")

class IdeaRequest(BaseModel):
    topic: str = Field(min_length=5, max_length=300)
    niche: str = Field(default="technology_documentary", max_length=80)
    languages: list[str] = Field(default=["en", "ru"], min_length=1, max_length=2)
    formats: list[str] = Field(default=["long", "shorts"], min_length=1, max_length=2)

    @classmethod
    def validate_options(cls, values):
        return values

@router.get("/media", response_class=HTMLResponse)
def media_dashboard():
    path = Path("web/media_hq.html")
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Media HQ dashboard not installed")
    return path.read_text(encoding="utf-8")

@router.get("/api/media/overview")
def overview(authorization: str | None = Header(default=None)):
    auth(authorization)
    jobs = media_db.list_jobs(50)
    return {"product": "AI Media HQ", "version": "1.0.0", "channel_count": 1,
            "languages": ["en", "ru"], "formats": ["long", "shorts"],
            "approval_mode": "hybrid", "jobs_total": len(jobs),
            "jobs_needs_review": sum(1 for j in jobs if j["status"] == "needs_review"),
            "agents": [{"id": a[0], "name": a[1], "description": a[2]} for a in media_db.AGENTS]}

@router.get("/api/media/agents")
def agents(authorization: str | None = Header(default=None)):
    auth(authorization)
    return {"agents": [{"id": a[0], "name": a[1], "description": a[2]} for a in media_db.AGENTS],
            "runs": media_db.list_agent_runs()}

@router.post("/api/media/ideas")
def create_idea(body: IdeaRequest, background_tasks: BackgroundTasks,
                authorization: str | None = Header(default=None)):
    auth(authorization)
    if any(x not in ("en", "ru") for x in body.languages):
        raise HTTPException(status_code=422, detail="Supported languages: en, ru")
    if any(x not in ("long", "shorts") for x in body.formats):
        raise HTTPException(status_code=422, detail="Supported formats: long, shorts")
    job_id = uuid.uuid4().hex[:12]
    payload = body.model_dump()
    media_db.create_job(job_id, payload)
    background_tasks.add_task(run_pipeline, job_id, payload)
    return {"id": job_id, "status": "queued", "approval_required": True}

@router.get("/api/media/jobs")
def jobs(limit: int = 30, authorization: str | None = Header(default=None)):
    auth(authorization)
    return {"jobs": media_db.list_jobs(max(1, min(limit, 100)))}

@router.get("/api/media/jobs/{job_id}")
def job(job_id: str, authorization: str | None = Header(default=None)):
    auth(authorization)
    item = media_db.get_job(job_id)
    if not item:
        raise HTTPException(status_code=404, detail="Job not found")
    item["agent_runs"] = media_db.list_agent_runs(job_id)
    return item

@router.post("/api/media/jobs/{job_id}/approve")
def approve(job_id: str, authorization: str | None = Header(default=None)):
    auth(authorization)
    item = media_db.get_job(job_id)
    if not item:
        raise HTTPException(status_code=404, detail="Job not found")
    if item["status"] != "needs_review":
        raise HTTPException(status_code=409, detail="Only completed drafts can be approved")
    media_db.update_job(job_id, approved=True, status="approved_for_production")
    return {"id": job_id, "status": "approved_for_production",
            "message": "Editorial draft approved. This does not publish to YouTube."}

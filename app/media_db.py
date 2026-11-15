import json
import sqlite3
from datetime import datetime, timezone
from app.config import DATABASE_PATH

AGENTS = [
    ("ceo", "AI CEO", "Orchestrates work, budgets and approval gates"),
    ("trend", "Trend Hunter", "Evaluates user-supplied topics; live trend research is not enabled yet"),
    ("research", "Research Agent", "Builds a research brief and marks claims requiring sources"),
    ("factcheck", "Fact Checker", "Flags unsupported claims; never invents citations"),
    ("writer", "Script Writer", "Writes original long-form documentary scripts"),
    ("story", "Story Director", "Creates a scene-by-scene storyboard"),
    ("localizer", "Localization Agent", "Adapts the approved story into English and Russian"),
    ("shorts", "Shorts Producer", "Creates short-form cutdowns from the long-form script"),
    ("voice", "Voice Agent", "Prepares narration text and voice direction"),
    ("editor", "Editor Agent", "Prepares an FFmpeg-ready edit manifest"),
    ("seo", "SEO Agent", "Creates titles, descriptions and thumbnail briefs"),
    ("qc", "Quality Control", "Checks completeness and keeps publication approval manual"),
]

def connect():
    db = sqlite3.connect(DATABASE_PATH, timeout=30)
    db.row_factory = sqlite3.Row
    return db

def now():
    return datetime.now(timezone.utc).isoformat()

def init_media_db():
    with connect() as db:
        db.execute("""CREATE TABLE IF NOT EXISTS media_jobs (
            id TEXT PRIMARY KEY, topic TEXT NOT NULL, niche TEXT NOT NULL,
            languages TEXT NOT NULL, formats TEXT NOT NULL, status TEXT NOT NULL,
            created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
            payload TEXT NOT NULL, result TEXT, error TEXT,
            approved INTEGER NOT NULL DEFAULT 0
        )""")
        db.execute("""CREATE TABLE IF NOT EXISTS media_agent_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT, job_id TEXT NOT NULL,
            agent_id TEXT NOT NULL, status TEXT NOT NULL, output TEXT,
            error TEXT, started_at TEXT NOT NULL, finished_at TEXT
        )""")

def create_job(job_id, payload):
    t = now()
    with connect() as db:
        db.execute("INSERT INTO media_jobs (id,topic,niche,languages,formats,status,created_at,updated_at,payload) VALUES (?,?,?,?,?,?,?,?,?)",
                   (job_id, payload["topic"], payload["niche"], json.dumps(payload["languages"]),
                    json.dumps(payload["formats"]), "queued", t, t, json.dumps(payload, ensure_ascii=False)))

def update_job(job_id, status=None, result=None, error=None, approved=None):
    fields, values = ["updated_at=?"], [now()]
    if status is not None: fields.append("status=?"); values.append(status)
    if result is not None: fields.append("result=?"); values.append(json.dumps(result, ensure_ascii=False))
    if error is not None: fields.append("error=?"); values.append(str(error)[:2000])
    if approved is not None: fields.append("approved=?"); values.append(1 if approved else 0)
    values.append(job_id)
    with connect() as db: db.execute("UPDATE media_jobs SET " + ",".join(fields) + " WHERE id=?", values)

def add_agent_run(job_id, agent_id, status, output=None, error=None, started_at=None):
    with connect() as db:
        db.execute("INSERT INTO media_agent_runs (job_id,agent_id,status,output,error,started_at,finished_at) VALUES (?,?,?,?,?,?,?)",
                   (job_id, agent_id, status, json.dumps(output, ensure_ascii=False) if output is not None else None,
                    str(error)[:1000] if error else None, started_at or now(), now()))

def _job(row):
    if not row: return None
    item = dict(row)
    item["languages"] = json.loads(item["languages"])
    item["formats"] = json.loads(item["formats"])
    item["payload"] = json.loads(item["payload"])
    item["result"] = json.loads(item["result"]) if item["result"] else None
    item["approved"] = bool(item["approved"])
    return item

def get_job(job_id):
    with connect() as db: return _job(db.execute("SELECT * FROM media_jobs WHERE id=?", (job_id,)).fetchone())

def list_jobs(limit=30):
    with connect() as db:
        return [_job(r) for r in db.execute("SELECT * FROM media_jobs ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()]

def list_agent_runs(job_id=None):
    with connect() as db:
        if job_id:
            rows = db.execute("SELECT * FROM media_agent_runs WHERE job_id=? ORDER BY id", (job_id,)).fetchall()
        else:
            rows = db.execute("SELECT * FROM media_agent_runs ORDER BY id DESC LIMIT 100").fetchall()
        out = []
        for r in rows:
            x = dict(r)
            x["output"] = json.loads(x["output"]) if x["output"] else None
            out.append(x)
        return out

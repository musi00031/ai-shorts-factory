import sqlite3,json
from datetime import datetime,timezone
from app.config import DATABASE_PATH
def connect():
 d=sqlite3.connect(DATABASE_PATH); d.row_factory=sqlite3.Row; return d
def init_db():
 with connect() as d: d.execute('CREATE TABLE IF NOT EXISTS jobs(id TEXT PRIMARY KEY,topic TEXT,language TEXT,duration INTEGER,status TEXT,created_at TEXT,updated_at TEXT,payload TEXT,result TEXT,error TEXT)')
def now(): return datetime.now(timezone.utc).isoformat()
def add_job(i,p):
 t=now()
 with connect() as d: d.execute('INSERT INTO jobs VALUES(?,?,?,?,?,?,?,?,?,?)',(i,p['topic'],p['language'],p['duration'],'queued',t,t,json.dumps(p,ensure_ascii=False),None,None))
def update_job(i,status=None,result=None,error=None):
 sets=['updated_at=?']; vals=[now()]
 for k,v in [('status',status),('result',json.dumps(result,ensure_ascii=False) if result is not None else None),('error',str(error)[:1500] if error is not None else None)]:
  if v is not None: sets.append(k+'=?'); vals.append(v)
 vals.append(i)
 with connect() as d: d.execute('UPDATE jobs SET '+','.join(sets)+' WHERE id=?',vals)
def conv(r):
 if not r:return None
 x=dict(r); x['payload']=json.loads(x['payload']); x['result']=json.loads(x['result']) if x['result'] else None; return x
def get_job(i):
 with connect() as d:return conv(d.execute('SELECT * FROM jobs WHERE id=?',(i,)).fetchone())
def list_jobs(n=30):
 with connect() as d:return [conv(x) for x in d.execute('SELECT * FROM jobs ORDER BY created_at DESC LIMIT ?',(n,)).fetchall()]

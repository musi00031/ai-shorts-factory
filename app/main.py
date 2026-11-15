import asyncio,uuid
from pathlib import Path
from fastapi import FastAPI,Header,HTTPException,BackgroundTasks
from fastapi.responses import FileResponse,HTMLResponse
from pydantic import BaseModel,Field
from app import db
from app.config import API_KEY
from app.agents import build_plan
from app.renderer import render_video
app=FastAPI(title='AI Shorts Factory',version='0.1.0'); db.init_db()
class JobRequest(BaseModel):
 topic:str=Field(min_length=2,max_length=300)
 script:str=Field(default='',max_length=6000)
 language:str=Field(default='ru',max_length=12)
 duration:int=Field(default=35,ge=10,le=90)
def auth(value):
 if API_KEY and value!=f'Bearer {API_KEY}': raise HTTPException(401,'Invalid API key')
async def process(i):
 j=db.get_job(i)
 try:
  db.update_job(i,status='planning'); plan=build_plan(j['payload']); db.update_job(i,status='rendering',result={'plan':plan})
  path=await asyncio.to_thread(render_video,i,plan,j['duration']); db.update_job(i,status='completed',result={'plan':plan,'video_path':path})
 except Exception as e: db.update_job(i,status='failed',error=repr(e))
@app.get('/health')
def health(): return {'ok':True}
@app.get('/',response_class=HTMLResponse)
def home(): return Path('web/index.html').read_text(encoding='utf-8')
@app.post('/api/jobs')
def create(body:JobRequest,bg:BackgroundTasks,authorization:str|None=Header(default=None)):
 auth(authorization); i=uuid.uuid4().hex[:12]; db.add_job(i,body.model_dump()); bg.add_task(process,i); return {'id':i,'status':'queued'}
@app.get('/api/jobs')
def jobs(limit:int=30): return {'jobs':db.list_jobs(max(1,min(limit,100)))}
@app.get('/api/jobs/{i}')
def status(i:str):
 j=db.get_job(i)
 if not j: raise HTTPException(404,'Job not found')
 return j
@app.get('/api/jobs/{i}/video')
def video(i:str):
 j=db.get_job(i); result=(j or {}).get('result') or {}; path=result.get('video_path')
 if not path or not Path(path).is_file(): raise HTTPException(404,'Video not ready')
 return FileResponse(path,media_type='video/mp4',filename=f'short-{i}.mp4')

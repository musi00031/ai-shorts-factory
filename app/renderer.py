import subprocess,tempfile,math
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from app.config import OUTPUT_DIR
W,H=1080,1920
def ft(n,b=False):
 p='/usr/share/fonts/truetype/dejavu/DejaVuSans'+('-Bold' if b else '')+'.ttf'
 return ImageFont.truetype(p,n) if Path(p).exists() else ImageFont.load_default()
def wrap(draw,s,f,maxw):
 out=[]; line=''
 for word in s.split():
  test=(line+' '+word).strip()
  if draw.textbbox((0,0),test,font=f)[2]<=maxw: line=test
  else:
   if line: out.append(line)
   line=word
 if line: out.append(line)
 return out or [s]
def card(text,i,total,path):
 im=Image.new('RGB',(W,H),(11,14,21)); d=ImageDraw.Draw(im)
 d.rounded_rectangle((65,90,1015,105),radius=8,fill=(48,55,68)); d.rounded_rectangle((65,90,65+int(950*i/total),105),radius=8,fill=(235,55,70))
 d.text((80,180),'AI SHORTS FACTORY',font=ft(34,True),fill=(235,65,80))
 f=ft(65,True); lines=wrap(d,text,f,900); y=(H-len(lines)*90)//2
 for line in lines:
  box=d.textbbox((0,0),line,font=f); d.text(((W-(box[2]-box[0]))//2,y),line,font=f,fill=(245,247,250)); y+=90
 d.text((80,1770),f'{i:02d} / {total:02d}',font=ft(28),fill=(145,155,170)); im.save(path,quality=92)
def render_video(job_id,plan,duration):
 scenes=plan.get('scenes') or [{'text':plan['script']}]; sec=max(3,math.ceil(duration/max(1,len(scenes))))
 with tempfile.TemporaryDirectory() as td:
  td=Path(td); n=len(scenes)
  for i,s in enumerate(scenes,1): card(s['text'],i,n,td/f'frame{i:03d}.jpg')
  out=OUTPUT_DIR/f'{job_id}.mp4'
  cmd=['ffmpeg','-y','-hide_banner','-loglevel','error','-framerate',f'1/{sec}','-i',str(td/'frame%03d.jpg'),'-t',str(duration),'-vf',f'scale={W}:{H},fps=30,format=yuv420p','-c:v','libx264','-preset','veryfast','-crf','23','-movflags','+faststart',str(out)]
  subprocess.run(cmd,check=True,capture_output=True,text=True); return str(out)

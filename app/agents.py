import re
from textwrap import shorten
def build_plan(p):
 topic=p['topic']; ru=p['language'].lower().startswith('ru')
 hook=(f'Ты удивишься: {topic}. Вот главное.' if ru else f'You may be surprised by {topic}. Here is the key.')
 default=(hook+'\n\nРазберём тему коротко и по делу. Обрати внимание на главную деталь: именно она меняет понимание всей истории. Запомни вывод и проверь его на практике. Подпишись — впереди новые разборы.' if ru else hook+'\n\nLet us break it down. Focus on the key detail most people overlook. It changes how the story makes sense. Remember the takeaway and follow for more.')
 script=p.get('script','').strip() or default
 parts=[x.strip() for x in re.split(r'(?<=[.!?])\s+|\n+',script) if x.strip()]
 scenes=[{'index':i+1,'text':shorten(x,width=115,placeholder='…')} for i,x in enumerate(parts[:8])]
 return {'director':{'format':'vertical explainer','target_duration':p['duration']},'hook':hook,'script':script,'scenes':scenes,'seo':{'title':shorten(topic,width=80),'description':topic,'hashtags':['#shorts','#reels','#факты'] if ru else ['#shorts','#reels','#facts']},'quality':{'ok':True,'warnings':['Basic prompt-based draft; verify factual claims before publishing.']}}

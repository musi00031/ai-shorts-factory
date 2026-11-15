import asyncio,os,aiohttp
from aiogram import Bot,Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
async def main():
 token=os.getenv('TELEGRAM_BOT_TOKEN','')
 if not token: raise RuntimeError('Set TELEGRAM_BOT_TOKEN')
 base=os.getenv('FACTORY_URL','http://localhost:8000').rstrip('/'); key=os.getenv('API_KEY',''); headers={'Authorization':'Bearer '+key} if key else {}
 bot=Bot(token); dp=Dispatcher()
 @dp.message(Command('start'))
 async def start(m:Message): await m.answer('AI Shorts Factory: отправь /make тема видео')
 @dp.message(Command('make'))
 async def make(m:Message):
  topic=(m.text or '').partition(' ')[2].strip()
  if len(topic)<2: await m.answer('Формат: /make тема видео'); return
  async with aiohttp.ClientSession() as s:
   async with s.post(base+'/api/jobs',json={'topic':topic},headers=headers) as r:
    d=await r.json(); await m.answer('Задача: '+str(d.get('id',d)))
 await dp.start_polling(bot)
if __name__=='__main__': asyncio.run(main())

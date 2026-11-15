import asyncio
import os

import aiohttp
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, Message


async def main():
    token = os.getenv('TELEGRAM_BOT_TOKEN', '').strip()
    if not token: raise RuntimeError('Set TELEGRAM_BOT_TOKEN in .env')
    base = os.getenv('FACTORY_URL', 'http://localhost:8000').rstrip('/')
    key = os.getenv('API_KEY', '').strip()
    if not key: raise RuntimeError('Set API_KEY in .env')
    headers = {'Authorization': 'Bearer ' + key}
    bot = Bot(token); dp = Dispatcher()
    @dp.message(Command('start', 'help'))
    async def start(m: Message):
        await m.answer('🎬 AI Shorts Factory\n/make тема — создать ролик\n/status ID — статус\n/get ID — получить MP4\n/latest — последние задачи')
    @dp.message(Command('make'))
    async def make(m: Message):
        topic = (m.text or '').partition(' ')[2].strip()
        if len(topic) < 2: await m.answer('Формат: /make тема видео'); return
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20)) as s:
            async with s.post(base + '/api/jobs', json={'topic': topic, 'language': 'ru', 'duration': 35}, headers=headers) as r:
                d = await r.json()
                if r.status >= 400: await m.answer('Ошибка: ' + str(d.get('detail', d))); return
        await m.answer(f"Задача создана: {d['id']}\nПроверка: /status {d['id']}")
    @dp.message(Command('status'))
    async def status(m: Message):
        job_id = (m.text or '').partition(' ')[2].strip()
        if not job_id: await m.answer('Формат: /status ID'); return
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20)) as s:
            async with s.get(base + '/api/jobs/' + job_id, headers=headers) as r:
                d = await r.json()
                if r.status >= 400: await m.answer('Ошибка: ' + str(d.get('detail', d))); return
        result = d.get('result') or {}; plan = result.get('plan') or {}
        text = f"Задача: {job_id}\nСтатус: {d['status']}\nТема: {d['topic']}"
        if d['status'] == 'completed': text += f'\nВидео готово. Отправь /get {job_id}'
        if d.get('error'): text += '\nОшибка: ' + d['error'][:700]
        await m.answer(text)
    @dp.message(Command('get'))
    async def get_video(m: Message):
        job_id = (m.text or '').partition(' ')[2].strip()
        if not job_id: await m.answer('Формат: /get ID'); return
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=120)) as s:
            async with s.get(base + '/api/jobs/' + job_id + '/video', headers=headers) as r:
                if r.status != 200:
                    try: d = await r.json(); detail = d.get('detail', 'Видео ещё не готово')
                    except Exception: detail = 'Видео ещё не готово'
                    await m.answer(str(detail)); return
                content = await r.read()
        if len(content) > 49 * 1024 * 1024: await m.answer('Файл превышает лимит Telegram-бота. Скачай его через веб-панель.'); return
        await m.answer_video(BufferedInputFile(content, filename=f'short-{job_id}.mp4'), caption=f'Готовый ролик {job_id}')
    @dp.message(Command('latest'))
    async def latest(m: Message):
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20)) as s:
            async with s.get(base + '/api/jobs?limit=5', headers=headers) as r:
                d = await r.json()
                if r.status >= 400: await m.answer('Ошибка: ' + str(d.get('detail', d))); return
        jobs = d.get('jobs', [])
        await m.answer('\n'.join(f"{j['id']} — {j['status']} — {j['topic']}" for j in jobs) or 'Задач пока нет.')
    await dp.start_polling(bot)

if __name__ == '__main__': asyncio.run(main())

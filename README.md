# AI Shorts Factory

Self-hosted MVP for vertical Shorts/Reels generation. FastAPI dashboard + API, prompt-based script planning, Pillow/FFmpeg rendering, SQLite history, optional Telegram bot, Docker deployment.

Run: copy .env.example to .env, set API_KEY, then `docker compose up --build -d`. Open http://localhost:8000.

The built-in agents create a starter script and storyboard; live trend research, LLM generation, fact-checking and the ChatGPT MCP bridge are roadmap items. Review facts before publishing.

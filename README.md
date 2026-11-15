# AI Shorts Factory

Self-hosted starter for creating vertical 9:16 Shorts/Reels from a topic or supplied script.

## Included
- FastAPI dashboard and REST API
- Prompt-based script planner and scene breakdown
- Pillow title cards and FFmpeg MP4 renderer
- SQLite job history
- Optional Telegram bot
- Docker Compose and GitHub Actions CI
- GitHub Codespaces devcontainer

## Run locally or on a Linux VPS
1. Copy `.env.example` to `.env`.
2. Set a long random `API_KEY` (required; API fails closed if missing).
3. Run `docker compose up --build -d`.
4. Open `http://localhost:8000`, enter the API key and connect.

## API
All endpoints except `/health` and the dashboard HTML require `Authorization: Bearer YOUR_API_KEY`.
- GET /health
- GET /
- POST /api/jobs
- GET /api/jobs
- GET /api/jobs/{id}
- GET /api/jobs/{id}/video

Example:
```bash
curl -X POST http://localhost:8000/api/jobs \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer YOUR_API_KEY' \
  -d '{"topic":"5 facts about space","language":"ru","duration":35}'
```

## Telegram
Set `TELEGRAM_BOT_TOKEN` in `.env`, then run:
```bash
docker compose --profile telegram up --build -d
```
The bot uses the same API key and talks to the app over the Docker network.

## Phone development
Open the repository in GitHub Codespaces from Chrome on Android. For rendering, use a Linux host/VPS with Docker and FFmpeg. Cloudflare Workers are suitable only for a lightweight proxy/control layer, not video rendering.

## Current limitations
This is an MVP, not a fully autonomous AI production suite. The planner uses deterministic templates; it does not perform live trend research, LLM writing, external fact-checking, stock-footage search, speech synthesis, or automatic publishing. Review factual claims and licensing before publishing. A ChatGPT MCP integration and OAuth authorization server are not included in this release.

Never commit `.env`, bot tokens, or API keys.

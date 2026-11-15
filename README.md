# AI Shorts Factory

Self-hosted starter for creating vertical 9:16 Shorts/Reels from a topic or supplied script.

## Included
- FastAPI dashboard and REST API
- Production roles: director, hook writer, scriptwriter, storyboard and SEO planner
- Optional AI generation through local Ollama or any OpenAI-compatible chat-completions API
- Deterministic fallback when no LLM is configured
- Pillow title cards and FFmpeg MP4 renderer
- SQLite job history, optional Telegram bot, Docker and GitHub Actions CI

## Start without paid APIs
1. Copy `.env.example` to `.env`.
2. Set a long random `API_KEY`.
3. Run `docker compose up --build -d`.
4. Open `http://localhost:8000`, enter the API key and connect.

## Enable local AI (optional)
The included Ollama profile runs a local model; it is not a paid API:
```bash
docker compose --profile llm up -d ollama
docker exec -it $(docker compose ps -q ollama) ollama pull qwen2.5:3b
```
Set these values in `.env`:
```env
LLM_BASE_URL=http://ollama:11434/v1/chat/completions
LLM_MODEL=qwen2.5:3b
LLM_API_KEY=
```
Then restart the app:
```bash
docker compose up -d --build app
```
Model download and inference require disk, RAM and CPU; first generation may be slow on a small VPS. You can instead point `LLM_BASE_URL` at another OpenAI-compatible endpoint and set `LLM_API_KEY`.

## API
All endpoints except `/health` and dashboard HTML require `Authorization: Bearer YOUR_API_KEY`.
- GET /health
- GET /
- POST /api/jobs
- GET /api/jobs
- GET /api/jobs/{id}
- GET /api/jobs/{id}/video

## Telegram
Set `TELEGRAM_BOT_TOKEN` in `.env`, then run `docker compose --profile telegram up --build -d`. The bot uses the same API key.

## Phone development
Open the repository in GitHub Codespaces from Chrome on Android. For rendering, use a Linux host/VPS with Docker and FFmpeg.

## Current limitations
The AI planner drafts content but does not independently verify factual claims, browse live trends, fetch stock footage, synthesize speech, or publish to social networks. Review claims and licensing before publishing. A ChatGPT remote MCP integration is not included: ChatGPT custom MCP connections require a compatible authenticated server and are configured through the web interface; write-tool availability depends on the ChatGPT plan/workspace. See OpenAI's current [custom MCP server guide](https://developers.openai.com/api/docs/guides/custom-mcp-server).

Never commit `.env`, bot tokens, or API keys.

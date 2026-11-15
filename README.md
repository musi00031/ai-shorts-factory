# AI Shorts Factory

Self-hosted starter for creating vertical 9:16 Shorts/Reels from a topic or supplied script.

## AI Media HQ v1.0

The repository also contains the first AI Media HQ scaffold: a hybrid-approval documentary workflow for one channel, English and Russian localization, long-form drafts and Shorts cutdowns. Open `/media` after deployment. See [the architecture guide](docs/AI_MEDIA_HQ_ARCHITECTURE.md). This is a draft-production system; fact-checking, asset licensing and human publication approval remain required.

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

## Multiple free-model providers

The planner supports an ordered fallback chain of OpenAI-compatible chat-completions providers. Configure `LLM_PROVIDERS` as a JSON array in `.env`; each entry uses `name`, `base_url`, `model`, and `api_key_env`. The app tries providers in order and moves to the next on rate limits, outages, or invalid responses. API keys stay in server environment variables and are never sent to the browser.

Example starter chain (check current model availability and free quotas before use):

```env
OPENROUTER_API_KEY=your_openrouter_key
GOOGLE_AI_API_KEY=your_google_ai_studio_key
LLM_PROVIDERS=[{"name":"OpenRouter Free Router","base_url":"https://openrouter.ai/api/v1/chat/completions","model":"openrouter/free","api_key_env":"OPENROUTER_API_KEY"},{"name":"Google AI Studio","base_url":"https://generativelanguage.googleapis.com/v1beta/openai/chat/completions","model":"gemini-2.5-flash","api_key_env":"GOOGLE_AI_API_KEY"}]
```

Other candidates with free tiers or limited free quotas include Groq, Cerebras, Hugging Face Inference Providers, NVIDIA NIM, and GitHub Models. They require separate keys and their limits/model identifiers can change. Do not treat free access as unlimited. Keep the deterministic renderer fallback enabled.

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
- GET /media (AI Media HQ dashboard)
- GET /api/media/overview
- GET /api/media/agents
- POST /api/media/ideas
- GET /api/media/jobs
- GET /api/media/jobs/{id}
- POST /api/media/jobs/{id}/approve

## Telegram

Set `TELEGRAM_BOT_TOKEN` in `.env`, then run `docker compose --profile telegram up --build -d`. The bot uses the same API key.

## Phone development

Open the repository in GitHub Codespaces from Chrome on Android. For rendering, use a Linux host/VPS with Docker and FFmpeg.

## Current limitations

The AI planner drafts content but does not independently verify factual claims, browse live trends, fetch stock footage, synthesize speech, or publish to social networks. Review claims and licensing before publishing. AI Media HQ v1.0 creates documentary drafts and Shorts cutdowns, but live source retrieval, fact-checking integrations, TTS, long-form rendering, YouTube OAuth upload and Analytics API integration remain later milestones.

A ChatGPT remote MCP integration is not included: ChatGPT custom MCP connections require a compatible authenticated server and are configured through the web interface; write-tool availability depends on the ChatGPT plan/workspace. See OpenAI's current [custom MCP server guide](https://developers.openai.com/api/docs/guides/custom-mcp-server).

Never commit `.env`, bot tokens, or API keys.

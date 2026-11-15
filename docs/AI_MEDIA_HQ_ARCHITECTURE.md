# AI Media HQ v1.0

## Approved operating profile
- One YouTube channel initially; English canonical edition and Russian localization.
- Long-form documentaries plus Shorts cutdowns.
- Hybrid autonomy: agents prepare drafts; a human approves editorial output and publication.
- No auto-publishing in v1.0.

## Services
- FastAPI: authenticated API and dashboard.
- Orchestrator: sequential, bounded agent workflow.
- SQLite: isolated media_jobs and media_agent_runs tables in the existing app database.
- LLM adapter: reuses the existing OpenAI-compatible provider fallback chain.
- FFmpeg: existing renderer remains available; long-form renderer is a later milestone.
- YouTube Data API/OAuth: future integration; no credentials are required for the current scaffold.

## Pipeline
1. Topic intake and suitability analysis.
2. Research brief with claims-to-verify and source types.
3. Original long-form script with [SOURCE NEEDED] markers.
4. Storyboard.
5. SEO and thumbnail brief.
6. Three Shorts cutdowns.
7. English/Russian localization.
8. Quality gate and human review.
9. Later: licensed asset acquisition, narration, long-form rendering, OAuth upload and analytics.

## Safety and editorial rules
- The research stage does not pretend to browse the live web and must not fabricate source URLs.
- Unsupported factual statements remain marked for verification.
- No upload occurs in this release. Approval only marks a draft as approved for the next production stage.
- Never store API keys in source control or browser local storage. Dashboard stores the API key in sessionStorage only.

## API
- GET /media
- GET /api/media/overview
- GET /api/media/agents
- POST /api/media/ideas
- GET /api/media/jobs
- GET /api/media/jobs/{id}
- POST /api/media/jobs/{id}/approve

## Deployment
The existing Docker image already copies app/ and web/. The existing deployment workflow already ships the repository to /opt/ai-shorts-factory. Existing secrets and .env are not changed by this feature branch. Merge after reviewing the diff and passing CI, then run the existing manual Deploy to VPS workflow.

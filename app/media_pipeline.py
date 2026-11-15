import json
import re
import uuid
from datetime import datetime, timezone
from app import media_db
from app.agents import _providers, _call_provider

def _ask(provider, role, task, payload):
    prompt = {
        "role": role,
        "task": task,
        "input": payload,
        "rules": [
            "Return one valid JSON object only.",
            "Do not invent facts, quotations, statistics, dates, or sources.",
            "Mark claims that require independent verification.",
            "Create original work; do not imitate a living creator or copy existing videos."
        ]
    }
    return _call_provider(provider, prompt)

def _fallback(payload):
    topic = payload["topic"]
    script = (
        f"OPENING\nWhat if the story behind {topic} is more complicated than it first appears?\n\n"
        f"CONTEXT\nThis documentary explores {topic}, separates established information from open questions, "
        "and explains why the subject matters.\n\n"
        "MAIN STORY\nBuild this section from independently verified primary and reputable secondary sources. "
        "For every factual claim, record the source, publication date and supporting passage.\n\n"
        "CONCLUSION\nSummarize what the evidence supports, what remains uncertain, and what viewers should investigate next."
    )
    return {
        "research": {"summary": f"Research brief required for: {topic}", "claims_to_verify": [topic], "sources": [], "status": "needs_human_sources"},
        "script": {"title": topic, "hook": f"What is really happening with {topic}?", "script": script, "estimated_minutes": 8, "status": "draft"},
        "storyboard": [{"scene": 1, "visual": "Original title sequence", "narration": "Opening hook"}, {"scene": 2, "visual": "Licensed footage or original graphics", "narration": "Context"}, {"scene": 3, "visual": "Evidence-led timeline and diagrams", "narration": "Main story"}, {"scene": 4, "visual": "Summary graphic", "narration": "Conclusion"}],
        "seo": {"title": topic, "description": "Original documentary. Sources and further reading will be added after fact-checking.", "tags": [], "thumbnail_brief": "One clear subject, high contrast, no misleading claims."},
        "shorts": [{"hook": f"The overlooked detail about {topic}", "script": f"Here is one question about {topic} worth investigating. Check the full documentary for the evidence.", "duration_seconds": 30}],
        "localizations": {},
        "production": {"voice_direction": "Clear documentary narration; measured pace.", "edit_notes": "Use licensed or original visuals; no unlicensed music.", "status": "not_rendered"},
        "quality": {"status": "needs_review", "checks": ["Add and verify sources", "Review script for factual accuracy", "Check visual and music licenses", "Human approval required before upload"]}
    }

def run_pipeline(job_id, payload):
    media_db.update_job(job_id, status="running")
    started = datetime.now(timezone.utc).isoformat()
    try:
        providers = _providers()
        provider = providers[0] if providers else None
        if not provider:
            result = _fallback(payload)
            for agent_id, _, _ in media_db.AGENTS:
                media_db.add_agent_run(job_id, agent_id, "completed" if agent_id in ("ceo","trend","research","writer","story","shorts","seo","qc") else "waiting",
                                       {"mode": "template_fallback"} if agent_id in ("ceo","trend","research","writer","story","shorts","seo","qc") else None)
        else:
            result = {}
            stages = [
                ("trend", "Trend analyst", "Evaluate topic suitability, audience promise, originality and risks. Do not claim live trend data. Return {angle, audience, differentiator, risks, score_1_to_10}.", {"topic": payload["topic"], "niche": payload["niche"], "languages": payload["languages"]}),
                ("research", "Documentary researcher", "Create a research brief with key questions, claims_to_verify and suggested primary-source types. Do not fabricate URLs or citations. Return {summary, claims_to_verify, source_types, open_questions}.", {"topic": payload["topic"], "angle": "Evidence-led explanatory documentary"}),
                ("writer", "Documentary scriptwriter", "Write an original 8-12 minute documentary script. Structure hook, context, chapters, conclusion. Include [SOURCE NEEDED] markers on factual claims. Return {title, hook, script, chapters, estimated_minutes}.", {"topic": payload["topic"], "research": result.get("research", {}), "target_minutes": 8}),
                ("story", "Story director", "Create 12-20 scene storyboard entries with narration_segment, visual_direction, on_screen_text and asset_type. Return {scenes:[...]}. Use original graphics or licensed footage.", {"script": result.get("script", {})}),
                ("seo", "YouTube SEO editor", "Create accurate, non-clickbait title options, description, tags and thumbnail brief. Return {titles, description, tags, thumbnail_brief}.", {"topic": payload["topic"], "script": result.get("script", {})}),
                ("shorts", "Shorts producer", "Create 3 distinct short cutdowns from the long-form script, each with hook, script, CTA and duration_seconds. No unsupported claims. Return {shorts:[...]}.", {"script": result.get("script", {})})
            ]
            for agent_id, role, task, data in stages:
                t = datetime.now(timezone.utc).isoformat()
                try:
                    output = _ask(provider, role, task, data)
                    result[agent_id if agent_id != "writer" else "script"] = output
                    media_db.add_agent_run(job_id, agent_id, "completed", output, started_at=t)
                except Exception as exc:
                    media_db.add_agent_run(job_id, agent_id, "failed", error=type(exc).__name__, started_at=t)
                    raise
            # Localize only after the canonical English script exists.
            localizations = {}
            for lang in payload["languages"]:
                if lang.lower().startswith("en"):
                    localizations["en"] = {"title": result["script"].get("title", payload["topic"]), "script": result["script"].get("script", "")}
                elif lang.lower().startswith("ru"):
                    t = datetime.now(timezone.utc).isoformat()
                    try:
                        loc = _ask(provider, "Professional Russian documentary localizer", "Adapt this English documentary for natural Russian narration. Preserve meaning, uncertainty and [SOURCE NEEDED] markers; do not add facts. Return {title, script}.", result["script"])
                        localizations["ru"] = loc
                        media_db.add_agent_run(job_id, "localizer", "completed", loc, started_at=t)
                    except Exception as exc:
                        media_db.add_agent_run(job_id, "localizer", "failed", error=type(exc).__name__, started_at=t)
                        raise
            result["localizations"] = localizations
            result["production"] = {"voice_direction": "Documentary narration; natural pacing and pronunciation review.", "edit_notes": "Use licensed/original visuals and cleared music. Render after editorial approval.", "status": "not_rendered"}
            result["quality"] = {"status": "needs_review", "checks": ["Researcher must attach verifiable sources", "Fact-check all factual claims", "Review both language versions", "Verify visual/music licenses", "Human approval required before YouTube upload"]}
            for agent_id in ("ceo", "factcheck", "voice", "editor", "qc"):
                media_db.add_agent_run(job_id, agent_id, "waiting", {"reason": "Requires next implementation stage or human review"})
        result["metadata"] = {"pipeline_version": "1.0.0", "provider": provider.get("name") if provider else "template", "created_at": started, "publication": "manual_approval_required"}
        media_db.update_job(job_id, status="needs_review", result=result)
    except Exception as exc:
        media_db.update_job(job_id, status="failed", error=f"{type(exc).__name__}: pipeline failed")

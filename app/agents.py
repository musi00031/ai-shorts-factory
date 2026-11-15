import json
import os
import re
import urllib.request
from textwrap import shorten


def _llm_plan(payload):
    endpoint = os.getenv("LLM_BASE_URL", "").strip()
    if not endpoint:
        return None
    model = os.getenv("LLM_MODEL", "qwen2.5:3b")
    api_key = os.getenv("LLM_API_KEY", "").strip()
    language = payload["language"]
    prompt = {
        "role": "You are a short-form video production team: director, hook writer, scriptwriter, storyboard artist and SEO editor.",
        "task": "Create a concise, engaging vertical video plan. Do not invent statistics, dates, quotes, or factual claims. If the topic needs research, explicitly mark claims that require verification.",
        "output": {
            "hook": "one opening hook",
            "script": "complete spoken script",
            "scenes": [{"index": 1, "text": "short on-screen caption"}],
            "seo": {"title": "short title", "description": "description", "hashtags": ["#shorts"]}
        },
        "constraints": {
            "topic": payload["topic"],
            "language": language,
            "duration_seconds": payload["duration"],
            "max_scenes": 8,
            "format": "Return JSON only, no markdown."
        }
    }
    if payload.get("script", "").strip():
        prompt["user_supplied_script"] = payload["script"].strip()
        prompt["task"] += " Preserve the user's supplied script; only structure it into scenes and improve metadata."
    body = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": prompt["role"]},
            {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)}
        ],
        "temperature": 0.7,
        "response_format": {"type": "json_object"}
    }).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = "Bearer " + api_key
    req = urllib.request.Request(endpoint, data=body, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=60) as response:
        data = json.loads(response.read().decode("utf-8"))
    raw = data["choices"][0]["message"]["content"]
    result = json.loads(raw)
    hook = str(result.get("hook") or "")[:400]
    script = str(result.get("script") or "")[:6000]
    scenes = result.get("scenes") or []
    if not script or not isinstance(scenes, list):
        raise ValueError("LLM returned an incomplete plan")
    clean_scenes = []
    for i, scene in enumerate(scenes[:8], 1):
        if isinstance(scene, dict) and scene.get("text"):
            clean_scenes.append({"index": i, "text": shorten(str(scene["text"]), 115, placeholder="…")})
    if not clean_scenes:
        clean_scenes = [{"index": i, "text": shorten(x.strip(), 115, placeholder="…")} for i, x in enumerate(re.split(r"(?<=[.!?])\\s+|\\n+", script), 1) if x.strip()][:8]
    seo = result.get("seo") if isinstance(result.get("seo"), dict) else {}
    return {
        "director": {"format": "vertical explainer", "target_duration": payload["duration"]},
        "hook": hook or script[:120],
        "script": script,
        "scenes": clean_scenes,
        "seo": {
            "title": str(seo.get("title") or payload["topic"])[:100],
            "description": str(seo.get("description") or payload["topic"])[:500],
            "hashtags": [str(x)[:40] for x in seo.get("hashtags", ["#shorts"])[:12]]
        },
        "quality": {"ok": True, "warnings": ["AI-generated content may contain errors; verify factual claims before publishing."], "engine": model}
    }


def build_plan(payload):
    try:
        plan = _llm_plan(payload)
        if plan:
            return plan
    except Exception as exc:
        llm_warning = f"LLM unavailable; deterministic fallback used ({type(exc).__name__})."
    else:
        llm_warning = "LLM not configured; deterministic fallback used."

    topic = payload["topic"]
    ru = payload["language"].lower().startswith("ru")
    hook = f"Ты удивишься: {topic}. Вот главное." if ru else f"You may be surprised by {topic}. Here is the key."
    default = (
        hook + "\\n\\nРазберём тему коротко и по делу. Обрати внимание на главную деталь: именно она меняет понимание всей истории. Запомни вывод и проверь его на практике. Подпишись — впереди новые разборы."
        if ru else
        hook + "\\n\\nLet us break it down. Focus on the key detail most people overlook. It changes how the story makes sense. Remember the takeaway and follow for more."
    )
    script = payload.get("script", "").strip() or default
    parts = [x.strip() for x in re.split(r"(?<=[.!?])\\s+|\\n+", script) if x.strip()]
    scenes = [{"index": i + 1, "text": shorten(x, 115, placeholder="…")} for i, x in enumerate(parts[:8])]
    return {
        "director": {"format": "vertical explainer", "target_duration": payload["duration"]},
        "hook": hook,
        "script": script,
        "scenes": scenes,
        "seo": {"title": shorten(topic, 80), "description": topic, "hashtags": ["#shorts", "#reels", "#факты"] if ru else ["#shorts", "#reels", "#facts"]},
        "quality": {"ok": True, "warnings": [llm_warning, "Verify factual claims before publishing."], "engine": "template"}
    }

import json
import os
import re
import urllib.request
from textwrap import shorten


def _providers():
    raw = os.getenv("LLM_PROVIDERS", "").strip()
    if raw:
        parsed = json.loads(raw)
        if not isinstance(parsed, list):
            raise ValueError("LLM_PROVIDERS must be a JSON array")
        return [p for p in parsed if isinstance(p, dict) and p.get("base_url") and p.get("model")]
    endpoint = os.getenv("LLM_BASE_URL", "").strip()
    if endpoint:
        return [{
            "name": "Legacy endpoint",
            "base_url": endpoint,
            "model": os.getenv("LLM_MODEL", "qwen2.5:3b"),
            "api_key_env": "",
        }]
    return []


def _call_provider(provider, prompt):
    api_key = os.getenv(str(provider.get("api_key_env") or ""), "").strip()
    body = json.dumps({
        "model": provider["model"],
        "messages": [
            {"role": "system", "content": prompt["role"]},
            {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)}
        ],
        "temperature": 0.7
    }).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = "Bearer " + api_key
    req = urllib.request.Request(provider["base_url"], data=body, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=int(provider.get("timeout", 60))) as response:
        data = json.loads(response.read().decode("utf-8"))
    raw = data["choices"][0]["message"]["content"]
    if isinstance(raw, list):
        raw = "".join(x.get("text", "") for x in raw if isinstance(x, dict))
    raw = str(raw).strip()
    raw = re.sub(r"^\`\`\`(?:json)?\s*|\s*\`\`\`$", "", raw, flags=re.I)
    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        start, end = raw.find("{"), raw.rfind("}")
        if start < 0 or end <= start:
            raise ValueError("Provider did not return a JSON object")
        result = json.loads(raw[start:end + 1])
    if not isinstance(result, dict):
        raise ValueError("Provider returned invalid plan")
    return result


def _llm_plan(payload):
    providers = _providers()
    if not providers:
        return None
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

    errors = []
    for provider in providers:
        try:
            result = _call_provider(provider, prompt)
            script = str(result.get("script") or "")[:6000]
            if not script:
                raise ValueError("LLM returned an empty script")
            scenes = result.get("scenes") or []
            if not isinstance(scenes, list):
                raise ValueError("LLM returned invalid scenes")
            clean_scenes = []
            for i, scene in enumerate(scenes[:8], 1):
                if isinstance(scene, dict) and scene.get("text"):
                    clean_scenes.append({"index": i, "text": shorten(str(scene["text"]), 115, placeholder="…")})
            if not clean_scenes:
                clean_scenes = [{"index": i, "text": shorten(x.strip(), 115, placeholder="…")} for i, x in enumerate(re.split(r"(?<=[.!?])\s+|\n+", script), 1) if x.strip()][:8]
            seo = result.get("seo") if isinstance(result.get("seo"), dict) else {}
            engine = str(provider.get("name") or provider["model"])
            return {
                "director": {"format": "vertical explainer", "target_duration": payload["duration"]},
                "hook": str(result.get("hook") or script[:120])[:400],
                "script": script,
                "scenes": clean_scenes,
                "seo": {
                    "title": str(seo.get("title") or payload["topic"])[:100],
                    "description": str(seo.get("description") or payload["topic"])[:500],
                    "hashtags": [str(x)[:40] for x in (seo.get("hashtags") or ["#shorts"])[:12]]
                },
                "quality": {"ok": True, "warnings": ["AI-generated content may contain errors; verify factual claims before publishing."], "engine": engine, "model": provider["model"]}
            }
        except Exception as exc:
            errors.append(f"{provider.get('name') or provider.get('model')}: {type(exc).__name__}")
    raise RuntimeError("All configured LLM providers failed: " + "; ".join(errors[:8]))


def build_plan(payload):
    try:
        plan = _llm_plan(payload)
        if plan:
            return plan
    except Exception as exc:
        llm_warning = f"LLM providers unavailable; deterministic fallback used ({type(exc).__name__})."
    else:
        llm_warning = "LLM not configured; deterministic fallback used."

    topic = payload["topic"]
    ru = payload["language"].lower().startswith("ru")
    hook = f"Ты удивишься: {topic}. Вот главное." if ru else f"You may be surprised by {topic}. Here is the key."
    default = (
        hook + "\n\nРазберём тему коротко и по делу. Обрати внимание на главную деталь: именно она меняет понимание всей истории. Запомни вывод и проверь его на практике. Подпишись — впереди новые разборы."
        if ru else
        hook + "\n\nLet us break it down. Focus on the key detail most people overlook. It changes how the story makes sense. Remember the takeaway and follow for more."
    )
    script = payload.get("script", "").strip() or default
    parts = [x.strip() for x in re.split(r"(?<=[.!?])\s+|\n+", script) if x.strip()]
    scenes = [{"index": i + 1, "text": shorten(x, 115, placeholder="…")} for i, x in enumerate(parts[:8])]
    return {
        "director": {"format": "vertical explainer", "target_duration": payload["duration"]},
        "hook": hook,
        "script": script,
        "scenes": scenes,
        "seo": {"title": shorten(topic, 80), "description": topic, "hashtags": ["#shorts", "#reels", "#факты"] if ru else ["#shorts", "#reels", "#facts"]},
        "quality": {"ok": True, "warnings": [llm_warning, "Verify factual claims before publishing."], "engine": "template"}
    }

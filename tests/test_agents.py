from app.agents import build_plan


def test_plan_has_hook_scenes_and_seo():
    plan = build_plan({"topic": "Космос", "language": "ru", "duration": 30, "script": "Первый факт. Второй факт."})
    assert plan["hook"]
    assert len(plan["scenes"]) == 2
    assert plan["seo"]["hashtags"]
    assert plan["director"]["target_duration"] == 30


def test_plan_uses_supplied_script():
    script = "Проверочный сценарий. Вторая фраза."
    plan = build_plan({"topic": "Тест", "language": "ru", "duration": 20, "script": script})
    assert plan["script"] == script

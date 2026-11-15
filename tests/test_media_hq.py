from app.media_db import AGENTS

def test_media_agent_roster_has_unique_ids():
    ids = [x[0] for x in AGENTS]
    assert len(ids) == 12
    assert len(ids) == len(set(ids))

def test_media_profile_has_expected_languages_and_formats():
    languages = ["en", "ru"]
    formats = ["long", "shorts"]
    assert languages == ["en", "ru"]
    assert formats == ["long", "shorts"]

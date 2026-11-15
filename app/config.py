import os
from pathlib import Path

API_KEY = os.getenv("API_KEY", "").strip()
DATABASE_PATH = os.getenv("DATABASE_PATH", "/data/factory.db")
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "/data/output"))
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "").strip()
LLM_MODEL = os.getenv("LLM_MODEL", "qwen2.5:3b")
LLM_API_KEY = os.getenv("LLM_API_KEY", "").strip()

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
Path(DATABASE_PATH).parent.mkdir(parents=True, exist_ok=True)

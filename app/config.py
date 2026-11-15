import os
from pathlib import Path
API_KEY=os.getenv('API_KEY','').strip()
DATABASE_PATH=os.getenv('DATABASE_PATH','/data/factory.db')
OUTPUT_DIR=Path(os.getenv('OUTPUT_DIR','/data/output'))
OUTPUT_DIR.mkdir(parents=True,exist_ok=True)
Path(DATABASE_PATH).parent.mkdir(parents=True,exist_ok=True)

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATABASE_DIR = BASE_DIR / "database"
DATABASE_FILE = Path(os.getenv("CHATBOT_DB_PATH", DATABASE_DIR / "chatbot.db"))

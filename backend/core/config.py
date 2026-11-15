import os
from pathlib import Path

from dotenv import load_dotenv

# Backend directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from backend/.env
load_dotenv(BASE_DIR / ".env")

# SQLite database file by default
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite:///{(BASE_DIR / 'prepbuddy.db').as_posix()}",
)

# Directory where uploaded documents will be stored
UPLOAD_DIR = Path(
    os.getenv("UPLOAD_DIR", str(BASE_DIR / "uploads"))
)

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
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


def _positive_int_setting(name: str, default: int) -> int:
    """Read a positive integer setting and fail fast for invalid config."""
    value = int(os.getenv(name, str(default)))

    if value <= 0:
        raise ValueError(f"{name} must be a positive integer")

    return value


# Upload and extraction limits. They can be overridden in backend/.env.
MAX_PDF_UPLOAD_BYTES = _positive_int_setting(
    "MAX_PDF_UPLOAD_BYTES",
    20 * 1024 * 1024,
)
UPLOAD_READ_CHUNK_BYTES = _positive_int_setting(
    "UPLOAD_READ_CHUNK_BYTES",
    1024 * 1024,
)
MAX_PDF_PAGE_COUNT = _positive_int_setting(
    "MAX_PDF_PAGE_COUNT",
    500,
)
MAX_EXTRACTED_TEXT_CHARS = _positive_int_setting(
    "MAX_EXTRACTED_TEXT_CHARS",
    5_000_000,
)

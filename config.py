"""Application configuration."""
from pathlib import Path

APP_NAME = "Library Management System"
APP_DIR = Path(__file__).resolve().parent
DATA_DIR = APP_DIR / "data"
DATABASE_PATH = DATA_DIR / "library.db"
DEFAULT_BORROWING_PERIOD = 14



from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parents[2]

env_file = BASE_DIR / ".env"
if env_file.is_file():
    for line_number, line in enumerate(
        env_file.read_text(encoding="utf-8").splitlines(),
        start=1,
    ):
        entry = line.strip()
        if not entry or entry.startswith("#"):
            continue

        key, separator, value = entry.partition("=")
        key = key.strip()
        if not separator or not key:
            raise ValueError(
                f"Invalid entry in Backend/.env on line {line_number}."
            )

        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        os.environ.setdefault(key, value)

from .base import *

DEBUG = True

ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
]

# Local frontend development ports.
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3002",
    "http://127.0.0.1:3002",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
CORS_ALLOW_CREDENTIALS = True

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3002",
    "http://127.0.0.1:3002",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
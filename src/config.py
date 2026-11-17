"""Project configuration values."""

import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Set the HIGHGUY_DB environment variable to use a different database file
# (handy for testing without touching your real memories).
DATABASE_PATH = Path(os.environ.get("HIGHGUY_DB", PROJECT_ROOT / "highguy_ai.db"))

# Private settings such as the API key live in .env (never committed to git).
ENV_FILE = PROJECT_ROOT / ".env"


def load_env_file():
    """Copy KEY=value lines from .env into the environment (existing values win)."""
    if not ENV_FILE.is_file():
        return
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"'))


def save_env_value(key, value):
    """Write or replace one KEY=value line in .env, and use it right away."""
    lines = []
    if ENV_FILE.is_file():
        lines = [line for line in ENV_FILE.read_text(encoding="utf-8").splitlines()
                 if not line.strip().startswith(key + "=")]
    if value:
        lines.append(f"{key}={value}")
        os.environ[key] = value
    else:
        os.environ.pop(key, None)
    ENV_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


load_env_file()

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


DEVPILOT_PROJECT_ROOT = Path(
    os.getenv(
        "DEVPILOT_PROJECT_ROOT",
        str(Path(__file__).resolve().parents[2]),
    )
).expanduser().resolve()

def get_required_env(name: str) -> str:
    value = os.getenv(name)

    if not value:
        raise RuntimeError(f"Required environment variable '{name}' is missing")

    return value


OPENROUTER_API_KEY = get_required_env("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv(
    "OPENROUTER_MODEL",
    "liquid/lfm-2.5-2.6b:free",
)
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
import os
from pathlib import Path

def get_project_root() -> Path:
    return Path(__file__).parent.parent.parent

def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)